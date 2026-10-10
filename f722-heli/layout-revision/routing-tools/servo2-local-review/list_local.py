exec(open('ordinary-routing/servo2-local-review/review_local.py').read().split('for xy in ')[0])
for o,l,g in local:
 if l=='F.Cu' and g.intersects(box(9.8,9.8,14.9,14.4)):
  print(json.dumps(brief(o,l,0)),list(g.bounds))
