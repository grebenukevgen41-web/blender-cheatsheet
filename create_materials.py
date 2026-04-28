"""
╔══════════════════════════════════════════════════════════════╗
║   BLENDER ARCHVIZ MATERIAL LIBRARY — 30 матеріалів          ║
║   Всі матеріали з текстурними нодами (Noise/Wave/Brick)      ║
║   Запусти: Blender → Scripting → Open → ▶ Run Script        ║
╚══════════════════════════════════════════════════════════════╝
"""
import bpy

# ── helpers ───────────────────────────────────────────────────
def make(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m

def N(mat, t, x=0, y=0, **kw):
    n = mat.node_tree.nodes.new(t)
    n.location = (x, y)
    for k, v in kw.items():
        if hasattr(n, k): setattr(n, k, v)
    return n

def L(mat, a, ao, b, bi):
    mat.node_tree.links.new(a.outputs[ao], b.inputs[bi])

def base(mat):
    out  = N(mat, 'ShaderNodeOutputMaterial', 600, 0)
    bsdf = N(mat, 'ShaderNodeBsdfPrincipled', 200, 0)
    L(mat, bsdf, 'BSDF', out, 'Surface')
    return bsdf

def tc_mp(mat, scale=1.0):
    tc = N(mat, 'ShaderNodeTexCoord', -900, 0)
    mp = N(mat, 'ShaderNodeMapping',  -720, 0)
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    L(mat, tc, 'UV', mp, 'Vector')
    return mp

def noise_bump(mat, mp, strength=0.5, scale=10.0, detail=8.0, x=-400):
    ns = N(mat, 'ShaderNodeTexNoise', x, -200)
    bm = N(mat, 'ShaderNodeBump',     x+200, -200)
    ns.inputs['Scale'].default_value   = scale
    ns.inputs['Detail'].default_value  = detail
    bm.inputs['Strength'].default_value = strength
    L(mat, mp, 'Vector', ns, 'Vector')
    L(mat, ns, 'Fac',    bm, 'Height')
    return bm  # connect bm → bsdf Normal

def set_bsdf(bsdf, color=None, metallic=None, roughness=None,
             ior=None, transmission=None, alpha=None,
             sheen=None, sheen_rough=None,
             emission_color=None, emission_strength=None,
             coat=None, specular=None):
    i = bsdf.inputs
    if color      is not None: i['Base Color'].default_value      = (*color,1)
    if metallic   is not None: i['Metallic'].default_value        = metallic
    if roughness  is not None: i['Roughness'].default_value       = roughness
    if ior        is not None: i['IOR'].default_value             = ior
    if transmission is not None: i['Transmission Weight'].default_value = transmission
    if alpha      is not None: i['Alpha'].default_value           = alpha
    if sheen      is not None: i['Sheen Weight'].default_value    = sheen
    if sheen_rough is not None: i['Sheen Roughness'].default_value= sheen_rough
    if emission_color is not None: i['Emission Color'].default_value = (*emission_color,1)
    if emission_strength is not None: i['Emission Strength'].default_value = emission_strength
    if coat       is not None: i['Coat Weight'].default_value     = coat
    if specular   is not None: i['Specular IOR Level'].default_value = specular

created = []

# ══════════════════════════════════════════════════════════════
#  1. МЕТАЛ
# ══════════════════════════════════════════════════════════════
def mk_metal(name, color, roughness, aniso=0.0, bump_str=0.05):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat)
    bm  = noise_bump(mat, mp, strength=bump_str, scale=20.0, detail=6.0)

    # Roughness variation via noise
    ns2 = N(mat, 'ShaderNodeTexNoise', -400, 100)
    ns2.inputs['Scale'].default_value = 15.0
    mr  = N(mat, 'ShaderNodeMath', -200, 100, operation='ADD')
    mr.inputs[1].default_value = roughness - 0.02
    L(mat, mp,  'Vector', ns2, 'Vector')
    L(mat, ns2, 'Fac',    mr,  0)
    L(mat, mr,  'Value',  bsdf,'Roughness')
    L(mat, bm,  'Normal', bsdf,'Normal')

    set_bsdf(bsdf, color=color, metallic=1.0)
    if aniso: bsdf.inputs['Anisotropic'].default_value = aniso
    created.append(name)

mk_metal('Metal_Chrome_Polished', (0.80,0.80,0.82), 0.03, bump_str=0.02)
mk_metal('Metal_Steel_Brushed',   (0.70,0.70,0.72), 0.28, aniso=0.7, bump_str=0.04)
mk_metal('Metal_Iron_Rusted',     (0.35,0.13,0.05), 0.82, bump_str=0.8)

# ══════════════════════════════════════════════════════════════
#  2. ДЕРЕВО — Wave (rings) + Noise distortion + Bump
# ══════════════════════════════════════════════════════════════
def mk_wood(name, c1, c2, roughness, ring_scale=4.5):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat)

    wave= N(mat, 'ShaderNodeTexWave',  -500, 100)
    ns  = N(mat, 'ShaderNodeTexNoise', -500,-100)
    mix = N(mat, 'ShaderNodeMixRGB',   -250, 100)
    bm  = N(mat, 'ShaderNodeBump',     -250,-100)

    wave.wave_type = 'RINGS'
    wave.inputs['Scale'].default_value      = ring_scale
    wave.inputs['Distortion'].default_value = 3.5
    wave.inputs['Detail'].default_value     = 8.0
    ns.inputs['Scale'].default_value        = 14.0
    ns.inputs['Detail'].default_value       = 6.0
    bm.inputs['Strength'].default_value     = 0.35
    mix.inputs['Color1'].default_value      = (*c1,1)
    mix.inputs['Color2'].default_value      = (*c2,1)

    L(mat, mp,   'Vector', wave,'Vector')
    L(mat, mp,   'Vector', ns,  'Vector')
    L(mat, wave, 'Color',  mix, 'Fac')
    L(mat, ns,   'Fac',    bm,  'Height')
    L(mat, mix,  'Color',  bsdf,'Base Color')
    L(mat, bm,   'Normal', bsdf,'Normal')
    set_bsdf(bsdf, roughness=roughness, specular=0.3)
    created.append(name)

mk_wood('Wood_Oak_Light',   (0.72,0.52,0.30),(0.85,0.66,0.42), 0.65, ring_scale=4)
mk_wood('Wood_Walnut_Dark', (0.20,0.10,0.05),(0.38,0.22,0.10), 0.60, ring_scale=5)
mk_wood('Wood_Pine_Raw',    (0.80,0.65,0.40),(0.92,0.78,0.55), 0.72, ring_scale=7)

# ══════════════════════════════════════════════════════════════
#  3. БЕТОН — Noise color + Bump + Roughness variation
# ══════════════════════════════════════════════════════════════
def mk_concrete(name, color, roughness, bump_str=0.8, ns_scale=8.0):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat)

    ns  = N(mat, 'ShaderNodeTexNoise', -550, 50)
    ramp= N(mat, 'ShaderNodeValToRGB', -350, 50)
    bm  = N(mat, 'ShaderNodeBump',     -350,-150)
    ns2 = N(mat, 'ShaderNodeTexNoise', -550,-200)

    ns.inputs['Scale'].default_value    = ns_scale
    ns.inputs['Detail'].default_value   = 14.0
    ns.inputs['Roughness'].default_value= 0.7
    ns2.inputs['Scale'].default_value   = 25.0
    bm.inputs['Strength'].default_value = bump_str

    c2 = (min(color[0]+.12,1),min(color[1]+.12,1),min(color[2]+.12,1))
    ramp.color_ramp.elements[0].color = (*color,1)
    ramp.color_ramp.elements[1].color = (*c2,1)

    L(mat, mp,  'Vector', ns,  'Vector')
    L(mat, mp,  'Vector', ns2, 'Vector')
    L(mat, ns,  'Fac',    ramp,'Fac')
    L(mat, ns2, 'Fac',    bm,  'Height')
    L(mat, ramp,'Color',  bsdf,'Base Color')
    L(mat, bm,  'Normal', bsdf,'Normal')
    set_bsdf(bsdf, roughness=roughness, specular=0.05)
    created.append(name)

mk_concrete('Concrete_Smooth',  (0.60,0.60,0.60), 0.88, bump_str=0.35, ns_scale=6)
mk_concrete('Concrete_Rough',   (0.45,0.44,0.42), 0.95, bump_str=1.2,  ns_scale=10)
mk_concrete('Concrete_Exposed', (0.52,0.50,0.47), 0.92, bump_str=0.8,  ns_scale=8)

# ══════════════════════════════════════════════════════════════
#  4. СКЛО — Transmission + Noise surface imperfections
# ══════════════════════════════════════════════════════════════
def mk_glass(name, color, roughness, ior=1.52):
    mat = make(name)
    mat.blend_method = 'HASHED'
    bsdf= base(mat)
    mp  = tc_mp(mat, scale=2.0)

    # Мікро-нерівності поверхні
    ns  = N(mat, 'ShaderNodeTexNoise', -400, -150)
    bm  = N(mat, 'ShaderNodeBump',     -200, -150)
    ns.inputs['Scale'].default_value    = 50.0
    ns.inputs['Detail'].default_value   = 4.0
    bm.inputs['Strength'].default_value = 0.05

    L(mat, mp, 'Vector', ns, 'Vector')
    L(mat, ns, 'Fac',    bm, 'Height')
    L(mat, bm, 'Normal', bsdf,'Normal')
    set_bsdf(bsdf, color=color, transmission=1.0, roughness=roughness, ior=ior, specular=0.5)
    created.append(name)

mk_glass('Glass_Clear',   (0.92,0.95,0.98), 0.00)
mk_glass('Glass_Frosted', (0.88,0.90,0.92), 0.18)
mk_glass('Glass_Tinted',  (0.20,0.45,0.30), 0.02)

# ══════════════════════════════════════════════════════════════
#  5. ТКАНИНА — Sheen + Noise fiber texture + Bump
# ══════════════════════════════════════════════════════════════
def mk_fabric(name, color, roughness, sheen, sheen_rough, ns_scale=20.0):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat, scale=3.0)

    # Fiber texture
    ns  = N(mat, 'ShaderNodeTexNoise', -550, 50)
    ramp= N(mat, 'ShaderNodeValToRGB', -330, 50)
    bm  = N(mat, 'ShaderNodeBump',     -330,-150)

    ns.inputs['Scale'].default_value    = ns_scale
    ns.inputs['Detail'].default_value   = 12.0
    ns.inputs['Roughness'].default_value= 0.8
    bm.inputs['Strength'].default_value = 0.4
    c2 = (min(color[0]+.08,1),min(color[1]+.08,1),min(color[2]+.08,1))
    ramp.color_ramp.elements[0].color   = (*color,1)
    ramp.color_ramp.elements[1].color   = (*c2,1)

    L(mat, mp,   'Vector', ns,   'Vector')
    L(mat, ns,   'Fac',    ramp, 'Fac')
    L(mat, ns,   'Fac',    bm,   'Height')
    L(mat, ramp, 'Color',  bsdf, 'Base Color')
    L(mat, bm,   'Normal', bsdf, 'Normal')
    set_bsdf(bsdf, roughness=roughness, sheen=sheen,
             sheen_rough=sheen_rough, specular=0.0)
    created.append(name)

mk_fabric('Fabric_Cotton_White',  (0.90,0.88,0.85), 0.92, 0.30, 0.60, ns_scale=18)
mk_fabric('Fabric_Velvet_Gray',   (0.28,0.28,0.32), 0.85, 1.00, 0.25, ns_scale=25)
mk_fabric('Fabric_Leather_Brown', (0.22,0.12,0.06), 0.55, 0.10, 0.50, ns_scale=12)

# ══════════════════════════════════════════════════════════════
#  6. МАРМУР — Wave veins + Noise distortion + Bump
# ══════════════════════════════════════════════════════════════
def mk_marble(name, c1, c2, roughness, vein_scale=3.0):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat)

    ns  = N(mat, 'ShaderNodeTexNoise', -550, 100)
    wave= N(mat, 'ShaderNodeTexWave',  -550,-100)
    mix = N(mat, 'ShaderNodeMixRGB',   -300, 100)
    bm  = N(mat, 'ShaderNodeBump',     -300,-100)

    ns.inputs['Scale'].default_value       = 5.0
    ns.inputs['Detail'].default_value      = 10.0
    wave.inputs['Scale'].default_value     = vein_scale
    wave.inputs['Distortion'].default_value= 2.5
    wave.inputs['Detail'].default_value    = 10.0
    bm.inputs['Strength'].default_value    = 0.08
    mix.inputs['Color1'].default_value     = (*c1,1)
    mix.inputs['Color2'].default_value     = (*c2,1)

    L(mat, mp,  'Vector', ns,  'Vector')
    L(mat, mp,  'Vector', wave,'Vector')
    L(mat, wave,'Color',  mix, 'Fac')
    L(mat, ns,  'Fac',    bm,  'Height')
    L(mat, mix, 'Color',  bsdf,'Base Color')
    L(mat, bm,  'Normal', bsdf,'Normal')
    set_bsdf(bsdf, roughness=roughness, specular=0.7)
    created.append(name)

mk_marble('Stone_Marble_White', (0.95,0.93,0.90),(0.55,0.52,0.48), 0.08)
mk_marble('Stone_Marble_Black', (0.05,0.05,0.06),(0.28,0.25,0.22), 0.10)
mk_marble('Stone_Granite_Gray', (0.45,0.43,0.42),(0.65,0.63,0.60), 0.40, vein_scale=9)

# ══════════════════════════════════════════════════════════════
#  7. ШТУКАТУРКА / ФАРБА — Noise + Bump
# ══════════════════════════════════════════════════════════════
def mk_plaster(name, color, roughness, bump_str=0.5, ns_scale=15.0):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat, scale=2.0)

    ns  = N(mat, 'ShaderNodeTexNoise', -400, 0)
    bm  = N(mat, 'ShaderNodeBump',     -200,-150)
    ns.inputs['Scale'].default_value    = ns_scale
    ns.inputs['Detail'].default_value   = 8.0
    ns.inputs['Roughness'].default_value= 0.6
    bm.inputs['Strength'].default_value = bump_str

    L(mat, mp, 'Vector', ns, 'Vector')
    L(mat, ns, 'Fac',    bm, 'Height')
    L(mat, bm, 'Normal', bsdf,'Normal')
    set_bsdf(bsdf, color=color, roughness=roughness, specular=0.04)
    created.append(name)

mk_plaster('Plaster_White_Smooth', (0.92,0.90,0.88), 0.90, bump_str=0.25, ns_scale=14)
mk_plaster('Plaster_White_Rough',  (0.88,0.86,0.83), 0.95, bump_str=1.0,  ns_scale=10)
mk_plaster('Paint_Glossy_White',   (0.95,0.95,0.95), 0.08, bump_str=0.05, ns_scale=30)

# ══════════════════════════════════════════════════════════════
#  8. ПІДЛОГА — Brick texture (плитка) + Noise bump
# ══════════════════════════════════════════════════════════════
def mk_floor(name, tile_color, grout_color, roughness, bump_str=0.2):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat, scale=0.5)

    brick= N(mat, 'ShaderNodeTexBrick', -500, 50)
    ns   = N(mat, 'ShaderNodeTexNoise', -500,-150)
    bm   = N(mat, 'ShaderNodeBump',     -280,-150)

    brick.inputs['Color1'].default_value   = (*tile_color,1)
    brick.inputs['Color2'].default_value   = (*tile_color,1)
    brick.inputs['Mortar'].default_value   = (*grout_color,1)
    brick.inputs['Scale'].default_value    = 5.0
    brick.inputs['Mortar Size'].default_value = 0.025
    ns.inputs['Scale'].default_value       = 25.0
    ns.inputs['Detail'].default_value      = 6.0
    bm.inputs['Strength'].default_value    = bump_str

    L(mat, mp,    'Vector', brick,'Vector')
    L(mat, mp,    'Vector', ns,   'Vector')
    L(mat, brick, 'Color',  bsdf, 'Base Color')
    L(mat, ns,    'Fac',    bm,   'Height')
    L(mat, bm,    'Normal', bsdf, 'Normal')
    set_bsdf(bsdf, roughness=roughness)
    created.append(name)

mk_floor('Floor_Ceramic_White', (0.88,0.87,0.85),(0.55,0.55,0.53), 0.15)
mk_floor('Floor_Ceramic_Dark',  (0.12,0.11,0.10),(0.20,0.20,0.18), 0.20)
mk_floor('Floor_Stone_Natural', (0.55,0.50,0.45),(0.38,0.36,0.33), 0.60, bump_str=0.4)

# ══════════════════════════════════════════════════════════════
#  9. ЕМІСІЯ + Noise variation яскравості
# ══════════════════════════════════════════════════════════════
def mk_emissive(name, color, strength):
    mat = make(name)
    bsdf= base(mat)
    mp  = tc_mp(mat, scale=5.0)

    ns  = N(mat, 'ShaderNodeTexNoise', -400, -150)
    mr  = N(mat, 'ShaderNodeMath',     -200, -150, operation='MULTIPLY')
    ns.inputs['Scale'].default_value   = 30.0
    ns.inputs['Detail'].default_value  = 2.0
    mr.inputs[1].default_value         = 0.08   # max ±8% variation

    L(mat, mp, 'Vector', ns, 'Vector')
    L(mat, ns, 'Fac',    mr, 0)
    # emission strength stays fixed — just slight color var via noise could be added later
    set_bsdf(bsdf, color=color, roughness=1.0,
             emission_color=color, emission_strength=strength)
    created.append(name)

mk_emissive('Emissive_Warm_Light', (1.00,0.95,0.85), 5.0)
mk_emissive('Emissive_Cool_Light', (0.85,0.90,1.00), 5.0)
mk_emissive('Emissive_LED_White',  (1.00,1.00,1.00), 10.0)

# ══════════════════════════════════════════════════════════════
#  ЗВІТ
# ══════════════════════════════════════════════════════════════
cats = [
    ('⚙️  Метал',      'Metal'),
    ('🪵  Дерево',     'Wood'),
    ('🏗  Бетон',      'Concrete'),
    ('🪟  Скло',       'Glass'),
    ('🛋  Тканина',    'Fabric'),
    ('🏛  Мармур',     'Stone'),
    ('🏠  Штукатурка', 'Plaster'),
    ('🏠  Фарба',      'Paint'),
    ('🟫  Підлога',    'Floor'),
    ('💡  Емісія',     'Emissive'),
]
print('\n' + '='*58)
print(f'  ✓  Створено {len(created)} матеріалів з текстурними нодами!')
print('='*58)
for label, prefix in cats:
    ms = [m for m in created if m.startswith(prefix)]
    if ms:
        print(f'\n  {label}:')
        for m in ms: print(f'    • {m}')
print('\n  Як застосувати:')
print('  Виділи об\'єкт → Material Properties → Browse Material')
print('='*58 + '\n')
