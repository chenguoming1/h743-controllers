"""Local diagnostic matcher only; original release exporter is untouched."""
from decimal import Decimal

def canon(feature):
 p,k,w,*xy=feature
 if k=='slot':
  a,b=sorted([xy[:2],xy[2:]])
  xy=a+b
 return p,k,Decimal(str(w)),*[Decimal(str(v)) for v in xy]

def match(expected,actual,half_grid=Decimal('0.0005')):
 # Inputs here come from decimal native JSON and decimal Excellon, so no
 # extra floating-point epsilon is needed or accepted.
 if len(expected)!=len(actual):raise ValueError('Census mismatch')
 source=[canon(x) for x in expected];used=set();rows=[]
 for a0 in actual:
  a=canon(a0);found=[]
  for i,e in enumerate(source):
   if a[:3]!=e[:3] or len(a)!=len(e):continue
   delta=[x-y for x,y in zip(a[3:],e[3:])]
   if all(abs(x)<=half_grid for x in delta):found.append((i,delta))
  if len(found)!=1:raise ValueError('Missing or ambiguous feature assignment')
  i,delta=found[0]
  if i in used:raise ValueError('Duplicate actual feature assignment')
  used.add(i);rows.append({'expected_index':i,'coordinate_delta_mm':[str(x) for x in delta]})
 if len(used)!=len(expected):raise ValueError('Incomplete expected coverage')
 return rows
