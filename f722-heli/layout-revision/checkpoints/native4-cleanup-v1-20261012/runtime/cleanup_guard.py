"""Exact cleanup declaration, independent of execution metadata."""

RECIPE_SHA='0dfd4ea5db3699d0e1bc94254ddeb24d4ad1f0a3063fea49476f0aa3e17c50f3'


PREVIOUS_SHA='29ab6e16895b42ef763b9891e7a6a304ef061d12545593971394a514feb4346b'


EXACT_TRIMS=[{'end':[29.378205,22.179418],'kind':'track','layer':'F.Cu','net':'PORT_C_TX_EXT','start':[28.754674,21.292007],'uuid':'5c47cb12-1b2e-51bd-b13a-67aecfb6dc76','width':.127},{'end':[28.051018,22.783107],'kind':'track','layer':'B.Cu','net':'PORT_C_TX_EXT','start':[27.20583,22.955774],'uuid':'449a10b1-dbb9-54de-ae5c-4f21c6a382c0','width':.127}]


def contract_binding():return {'schema':'f722-exact-TX-unused-arm-cleanup/v1','recipe_sha256':RECIPE_SHA,'predecessor_recipe_sha256':PREVIOUS_SHA,'additional_source_cuts':10,'additional_tracks':2,'additional_vias':0,'net':'PORT_C_TX_EXT','all_94_previous_additions_unchanged':True,'fixed_trim_geometry':EXACT_TRIMS,'no_pose_pad_net_CORE_or_GND_changes':True}

