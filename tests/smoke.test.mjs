import { test } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { apply, loadSkill, parseFrontmatter } from '../lib/index.js'

const pkgRoot = decodeURIComponent(new URL('..', import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1')

test('parseFrontmatter extracts name/description/whenToUse', () => {
  const { meta, body } = parseFrontmatter(
    '---\nname: demo\ndescription: "A demo: yes"\nwhenToUse: when testing\n---\n\n# Demo\n',
  )
  assert.equal(meta.name, 'demo')
  assert.equal(meta.description, 'A demo: yes')
  assert.equal(meta.whenToUse, 'when testing')
  assert.match(body, /# Demo/)
})

test('loadSkill reads the bundled skill and points at its resources', () => {
  const skill = loadSkill()
  assert.equal(skill.name, 'hoi4-modding')
  assert.ok(skill.description.length > 40)
  assert.match(skill.content, /# HOI4 1\.19\.3/)
  assert.equal(skill.provider, 'hoi4-modding')
  assert.equal(skill.source, 'bundled')
  assert.equal(skill.resourceBase.kind, 'directory')
  assert.ok(existsSync(join(skill.resourceBase.path, 'references', 'cheatsheet.md')))
  assert.ok(existsSync(join(skill.resourceBase.path, 'scripts', 'hoi4_lint.py')))
})

test('apply registers exactly one skill into ctx.skills', () => {
  const registered = []
  const ctx = { skills: { register: (skill) => registered.push(skill) }, logger: { warn() {} } }
  apply(ctx)
  assert.equal(registered.length, 1)
  assert.equal(registered[0].name, 'hoi4-modding')
  assert.ok(registered[0].content.includes('## 1. 铁律'))
})

test('package declares a dsh bundle patch that inserts the plugin', () => {
  const pkg = JSON.parse(readFileSync(join(pkgRoot, 'package.json'), 'utf8'))
  assert.equal(pkg.name, 'dsh-hoi4-modding')
  assert.equal(pkg.dsh.bundle.patch, './cordis.patch.yml')
  const patch = readFileSync(join(pkgRoot, 'cordis.patch.yml'), 'utf8')
  assert.match(patch, /id: hoi4-modding/)
  assert.match(patch, /name: dsh-hoi4-modding/)
})

test('tech tree UI reference and scripts are bundled', () => {
  const skill = loadSkill()
  const base = skill.resourceBase.path
  assert.ok(existsSync(join(base, 'references', 'tech-tree-ui.md')))
  for (const f of [
    'tech_tree_audit.py',
    'tech_folder_available.py',
    'item_sprite_check.py',
    'errorlog_triage.py',
  ]) {
    assert.ok(existsSync(join(base, 'scripts', f)), f + ' missing')
  }
  assert.match(skill.content, /original_tag/)
  assert.match(skill.content, /force_use_small_tech_layout/)
})


test('tank designer references and scripts are bundled', () => {
  const skill = loadSkill()
  const base = skill.resourceBase.path
  for (const f of [
    'references/tank-designer.md',
    'references/tank-models-3d.md',
    'references/icon-dds-pipeline.md',
  ]) {
    assert.ok(existsSync(join(base, f)), f + ' missing')
  }
  for (const f of ['tank_designer_probe.py', 'tank_designer_layout.py', 'tech_icon_import.py']) {
    assert.ok(existsSync(join(base, 'scripts', f)), f + ' missing')
  }
  assert.match(skill.content, /tank_designer_layout\.py/)
  assert.match(skill.content, /173×77|173x77/)
})

test('scripted GUI/topbar reference and 18-slot preset are bundled', () => {
  const skill = loadSkill()
  const base = skill.resourceBase.path
  const ref = join(base, 'references', 'scripted-gui-and-topbar.md')
  assert.ok(existsSync(ref), 'scripted GUI reference missing')
  const refText = readFileSync(ref, 'utf8')
  assert.match(refText, /containerWindowType/)
  assert.match(refText, /<button名>_click|<button名>_click|_click/)
  assert.match(refText, /top_bar|production_tab/)
  assert.match(skill.content, /scripted-gui-and-topbar\.md/)
  const script = readFileSync(join(base, 'scripts', 'tank_designer_layout.py'), 'utf8')
  assert.match(script, /18-compact/)
  assert.match(script, /row_slots=\(7, 4, 7\)/)
})

test('CJK font reference and font_audit script are bundled', () => {
  const skill = loadSkill()
  const base = skill.resourceBase.path
  const ref = join(base, 'references', 'fonts-and-cjk.md')
  assert.ok(existsSync(ref), 'fonts-and-cjk.md missing')
  const text = readFileSync(ref, 'utf8')
  assert.match(text, /core_chinese\.gfx/)
  assert.match(text, /bitmapfont_override/)
  assert.match(text, /hoi_16mbs/)
  assert.match(text, /hoi_14mbs/)
  const script = join(base, 'scripts', 'font_audit.py')
  assert.ok(existsSync(script), 'font_audit.py missing')
  const py = readFileSync(script, 'utf8')
  assert.match(py, /FALLBACK_SUPPORTED/)
  assert.match(py, /FONT_RE = re\.compile/)
  assert.match(skill.content, /font_audit\.py/)
  assert.match(skill.content, /fonts-and-cjk\.md/)
})

test('workshop mod survey and agent team playbook are bundled', () => {
  const skill = loadSkill()
  const base = skill.resourceBase.path
  const survey = join(base, 'references', 'vanilla-mod-survey.md')
  const teams = join(base, 'references', 'agent-teams-playbook.md')
  assert.ok(existsSync(survey), 'vanilla-mod-survey.md missing')
  assert.ok(existsSync(teams), 'agent-teams-playbook.md missing')
  const s = readFileSync(survey, 'utf8')
  for (const needle of ['Black ICE', 'Millennium Dawn', 'TNO', 'duplicate_archetypes', 'gui_category', 'parent_window_token']) {
    assert.ok(s.includes(needle), needle + ' missing in survey')
  }
  const t = readFileSync(teams, 'utf8')
  assert.match(t, /survey/)
  assert.match(t, /build/)
  assert.match(t, /audit/)
  assert.match(t, /写域|文件所有权/)
  assert.match(skill.content, /vanilla-mod-survey\.md|agent-teams-playbook\.md/)
})
