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
