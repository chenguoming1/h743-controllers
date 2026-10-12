"""Exact saved-report cleanup review helpers."""
import review_partial_rx_progress as rx

TRIMS={'5c47cb12-1b2e-51bd-b13a-67aecfb6dc76','449a10b1-dbb9-54de-ae5c-4f21c6a382c0'}


def pairs(groups):return {tuple(sorted((a,b))) for group in groups for i,a in enumerate(group) for b in group[i+1:]}


def partitions(prior,current):
 before={r['net']:r for r in prior['all_physical_nets']};after={r['net']:r for r in current['all_physical_nets']}
 rx.require(set(before)==set(after),'Complete raw native5 net inventory required')
 return [{'net':net,'raw_native5_pad_partition':before[net]['candidate_raw_pad_partition'],'cleanup_pad_partition':after[net]['candidate_raw_pad_partition'],'lost_pad_pairs':sorted(pairs(before[net]['candidate_raw_pad_partition'])-pairs(after[net]['candidate_raw_pad_partition'])),'new_pad_pairs':sorted(pairs(after[net]['candidate_raw_pad_partition'])-pairs(before[net]['candidate_raw_pad_partition'])),'UUID_or_role_permutation_used':False} for net in sorted(before)]


def trim_review(report):
 endpoints=[r for r in report['new_track_endpoint_support'] if r['track_uuid'] in TRIMS]
 fragments=[r for net in report['all_physical_nets'] for r in net['new_record_fragments'] if r['uuid'] in TRIMS]
 exact_endpoints={u:{tuple(r['endpoint']) for r in endpoints if r['track_uuid']==u} for u in TRIMS}
 expected={'5c47cb12-1b2e-51bd-b13a-67aecfb6dc76':{(28.754674,21.292007),(29.378205,22.179418)},'449a10b1-dbb9-54de-ae5c-4f21c6a382c0':{(27.20583,22.955774),(28.051018,22.783107)}}
 ok=len(endpoints)==4 and exact_endpoints==expected and all(r['passed'] for r in endpoints) and len(fragments)==2 and {r['uuid'] for r in fragments}==TRIMS and all(r['every_fragment_reaches_real_pad'] for r in fragments)
 return {'exact_trim_UUIDs':sorted(TRIMS),'all_four_exact_trim_endpoints':endpoints,'both_trim_fragment_obligations':fragments,'passed':ok}

