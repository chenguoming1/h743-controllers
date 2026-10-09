#!/usr/bin/env python3
"""Audit numeric inlining at each planning-margin source line in local class files."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = 'app/freerouting/autoroute'


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        result = self.data[self.pos:self.pos + count]
        assert len(result) == count, 'Truncated class file'
        self.pos += count
        return result

    def u1(self): return self.take(1)[0]
    def u2(self): return struct.unpack('>H', self.take(2))[0]
    def u4(self): return struct.unpack('>I', self.take(4))[0]


def attributes(reader, pool):
    return [(pool[reader.u2()], reader.take(reader.u4())) for _ in range(reader.u2())]


def parse_class(data):
    r = Reader(data)
    assert r.u4() == 0xCAFEBABE
    r.take(4)
    pool, count, index = [None], r.u2(), 1
    while index < count:
        tag = r.u1()
        if tag == 1: value = r.take(r.u2()).decode('utf-8')
        elif tag == 3: value = struct.unpack('>i', r.take(4))[0]
        elif tag == 4: value = struct.unpack('>f', r.take(4))[0]
        elif tag == 5: value = struct.unpack('>q', r.take(8))[0]
        elif tag == 6: value = struct.unpack('>d', r.take(8))[0]
        elif tag in (7, 8, 16, 19, 20): value = ('ref', r.u2())
        elif tag in (9, 10, 11, 12, 17, 18): value = ('pair', r.u2(), r.u2())
        elif tag == 15: value = ('handle', r.u1(), r.u2())
        else: raise AssertionError(f'Unhandled constant-pool tag {tag}')
        pool.append(value)
        index += 1
        if tag in (5, 6):
            pool.append(None)
            index += 1
    r.take(6)
    r.take(2 * r.u2())
    fields = {}
    for _ in range(r.u2()):
        r.u2(); name = pool[r.u2()]; r.u2()
        for key, value in attributes(r, pool):
            if key == 'ConstantValue': fields[name] = pool[Reader(value).u2()]
    methods = []
    for _ in range(r.u2()):
        r.u2(); name = pool[r.u2()]; descriptor = pool[r.u2()]
        for key, value in attributes(r, pool):
            if key != 'Code': continue
            c = Reader(value); c.take(4); code = c.take(c.u4()); c.take(8 * c.u2())
            lines = []
            for attr, payload in attributes(c, pool):
                if attr == 'LineNumberTable':
                    numbers = Reader(payload)
                    lines = [(numbers.u2(), numbers.u2()) for _ in range(numbers.u2())]
            methods.append((name, descriptor, code, lines))
    return pool, fields, methods


def instructions(code, pool):
    one = {0x10, 0x12, *range(0x15, 0x1a), *range(0x36, 0x3b), 0xa9, 0xbc}
    two = {0x11, 0x13, 0x14, 0x84, *range(0x99, 0xa9), *range(0xb2, 0xb9), 0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7}
    pc = 0
    while pc < len(code):
        start, opcode = pc, code[pc]
        pc += 1
        value = None
        if 0x02 <= opcode <= 0x08: value = opcode - 3
        elif opcode in (0x09, 0x0a): value = opcode - 9
        elif opcode in (0x0b, 0x0c, 0x0d): value = float(opcode - 11)
        elif opcode in (0x0e, 0x0f): value = float(opcode - 14)
        elif opcode == 0x10: value = struct.unpack('>b', code[pc:pc+1])[0]
        elif opcode == 0x11: value = struct.unpack('>h', code[pc:pc+2])[0]
        elif opcode == 0x12: value = pool[code[pc]]
        elif opcode in (0x13, 0x14): value = pool[struct.unpack('>H', code[pc:pc+2])[0]]
        if opcode in one: pc += 1
        elif opcode in two: pc += 2
        elif opcode in (0xb9, 0xba, 0xc8, 0xc9): pc += 4
        elif opcode == 0xc5: pc += 3
        elif opcode == 0xc4:
            pc += 5 if code[pc] == 0x84 else 3
        elif opcode in (0xaa, 0xab):
            pc = (pc + 3) & ~3
            if opcode == 0xaa:
                _, low, high = struct.unpack('>iii', code[pc:pc+12])
                pc += 12 + 4 * (high - low + 1)
            else:
                _, count = struct.unpack('>ii', code[pc:pc+8])
                pc += 8 + 8 * count
        assert pc <= len(code), 'Invalid instruction length'
        yield start, opcode, value


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    engine_path = ROOT / 'build' / PACKAGE / 'AutorouteEngine.class'
    _, fields, _ = parse_class(engine_path.read_bytes())
    assert fields['TRACE_WIDTH_TOLERANCE'] == 18, 'Compiled engine still has an old planning margin'
    report = {'passed': True, 'planning_margin_engine_units': 18,
              'classpath_order': ['build', 'vendor/freerouting-2.1.0.jar'],
              'engine_class_sha256': digest(engine_path), 'call_sites': []}
    consumers = {'LocateFoundConnectionAlgo45Degree': 1, 'LocateFoundConnectionAlgoAnyAngle': 1,
                 'ExpansionDoor': 1, 'MazeSearchAlgo': 2}
    for name, expected_count in consumers.items():
        source = ROOT / 'src' / PACKAGE / f'{name}.java'
        compiled = ROOT / 'build' / PACKAGE / f'{name}.class'
        assert compiled.is_file(), f'Missing local override: {compiled}'
        reference_lines = [i for i, line in enumerate(source.read_text().splitlines(), 1)
                           if 'AutorouteEngine.TRACE_WIDTH_TOLERANCE' in line]
        assert len(reference_lines) == expected_count, f'Unexpected call-site count in {name}'
        pool, _, methods = parse_class(compiled.read_bytes())
        for line in reference_lines:
            found = []
            for method, descriptor, code, lines in methods:
                for offset, opcode, value in instructions(code, pool):
                    preceding = [(start, number) for start, number in lines if start <= offset]
                    current_line = max(preceding)[1] if preceding else None
                    if current_line == line and value == 18:
                        found.append({'method': method, 'descriptor': descriptor,
                                      'bytecode_offset': offset, 'opcode_hex': hex(opcode), 'numeric_constant': value})
            assert found, f'No compiled 18 at {name}.java:{line}; stale or mismatched bytecode'
            report['call_sites'].append({'class': name, 'source_line': line,
                                        'source_sha256': digest(source), 'class_sha256': digest(compiled),
                                        'compiled_evidence': found})
    assert len(report['call_sites']) == 5
    insertion = json.loads((ROOT / 'tests/insertion-gap-result-margin18.json').read_text())
    nominal = insertion['configuration']['matrix_nominal_engine_units']
    safety = insertion['configuration']['matrix_with_safety_engine_units']
    assert nominal == 12700 and safety == 12716
    fast_max_x = max(section['bounds_engine'][2] for guard in insertion['guard_tree_geometry']
                     for section in guard['fast_compensated_sections'])
    planned_x = fast_max_x + 6350 + (nominal + 1) // 2 + 18
    assert planned_x == 4116570
    matching = [case for case in insertion['cases'] if round(case['segment_mm'][0][0] * 100000) == planned_x]
    assert len(matching) == 1
    case = matching[0]
    assert case['full_insertion'] and case['spring_over_result'] == 'unchanged'
    assert all(check['allowed'] for check in case['shove_checks_on_original_segment'])
    assert case['guard_geometry_unchanged']
    zero = next(case for case in insertion['cases'] if case['outward_shift_engine_units'] == 0)
    assert not zero['full_insertion'] and zero['spring_over_result'] == 'null'
    report['insertion_fixture_proof'] = {'report_sha256': digest(ROOT / 'tests/insertion-gap-result-margin18.json'),
        'source_board_sha256': insertion['source_board_sha256'], 'fixture_sha256': insertion['fixture_sha256'],
        'planned_x_engine': planned_x, 'planned_x_mm': planned_x / 100000,
        'outward_shift_engine_units': case['outward_shift_engine_units'],
        'full_insertion': True, 'spring_over_unchanged': True, 'shove_checks_passed': True,
        'original_segment_still_rejected': True, 'nominal_clearance_engine_units': nominal,
        'insertion_clearance_with_safety_engine_units': safety, 'guard_geometry_unchanged': True}
    destination = ROOT / 'tests/compiled-planning-margin18-proof.json'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'compiled_call_sites': 5, 'compiled_consumer_classes': 4,
                      'planned_x_engine': planned_x, 'full_insertion': True, 'report': str(destination)}))


if __name__ == '__main__':
    main()
