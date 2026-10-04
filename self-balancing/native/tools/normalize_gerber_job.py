#!/usr/bin/python3
"""Correct KiCad9 optional job metadata from the emitted X2 files and approved design rules."""
from pathlib import Path
import json,re,hashlib

def normalize(directory, review, targets):
 directory=Path(directory);review=Path(review);paths=list(directory.glob('*.gbrjob'));assert len(paths)==1
 jobpath=paths[0];original=jobpath.read_bytes();job=json.loads(original);rows=job['FilesAttributes'];assert len(rows)==13
 corrections=[];functions={}
 for row in rows:
  name=row['Path'];assert Path(name).name==name and (directory/name).is_file()
  text=(directory/name).read_text();m=re.search(r'%TF.FileFunction,([^*]+)\*%',text);assert m;function=m.group(1);functions[name]=function
  if function.startswith('Copper,'):
   if row['FileFunction']!=function:corrections.append({'file':name,'field':'FileFunction','before':row['FileFunction'],'after':function});row['FileFunction']=function
  else:
   aliases={'Paste,Top':'SolderPaste,Top','Paste,Bot':'SolderPaste,Bot','Soldermask,Top':'SolderMask,Top','Soldermask,Bot':'SolderMask,Bot','Profile,NP':'Profile','Legend,Top':'Legend,Top','Legend,Bot':'Legend,Bot'}
   assert aliases.get(function)==row['FileFunction'],(name,function,row['FileFunction'])
 assert {v for v in functions.values() if v.startswith('Copper,')}=={'Copper,L1,Top','Copper,L2,Inr','Copper,L3,Inr','Copper,L4,Inr','Copper,L5,Inr','Copper,L6,Bot'}
 edge=next(name for name,value in functions.items() if value=='Profile,NP');text=(directory/edge).read_text();assert '%MOMM*%' in text and '%FSLAX46Y46*%' in text
 points=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[123]\*',text)];bounds=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)];assert bounds==[0.,0.,38.,38.]
 size={'X':38.,'Y':38.};corrections.append({'field':'GeneralSpecs.Size','before':job['GeneralSpecs']['Size'],'after':size,'basis':'Profile centerline extrema; excludes plotted stroke width'});job['GeneralSpecs']['Size']=size
 for rules in job['DesignRules']:
  old=dict(rules);rules['TrackToTrack']=targets['minimum_trace_spacing_mm'];rules['MinLineWidth']=targets['minimum_trace_width_mm'];rules['PadToPad']=.15;rules['PadToTrack']=.15
  if old!=rules:corrections.append({'field':'DesignRules','before':old,'after':rules})
 assert job['GeneralSpecs']['LayerNumber']==6
 (review/'generated-gerber-job-original.json').write_bytes(original);jobpath.write_text(json.dumps(job,indent=2)+'\n')
 sha=lambda data:hashlib.sha256(data).hexdigest();proof={'original_sha256':sha(original),'normalized_sha256':sha(jobpath.read_bytes()),'corrections':corrections,'actual_X2_file_functions':functions,'outline_centerline_bounds_mm':bounds,'scope':'Optional job metadata only; no Gerber copper/mask/paste/outline or drill bytes changed. Non-copper job vocabulary retains its emitted aliases.'};(review/'gerber-job-normalization.json').write_text(json.dumps(proof,indent=2)+'\n');return proof
