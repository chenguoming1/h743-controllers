exec(open('ordinary-routing/servo2-local-review/review_local.py').read().split('for xy in ')[0])
for o,l,g in local:
 if l=='B.Cu' and g.intersects(box(10.8,9.8,14.9,13.4)):
  print(json.dumps(brief(o,l,0)),list(g.bounds))
