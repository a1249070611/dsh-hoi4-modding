/**
 * dsh-hoi4-modding — bundle the HOI4 modding skill into DeepSeek Harness.
 *
 * The skill files live in `skills/hoi4-modding/` and stay the single source of
 * truth (SKILL.md + references + scripts). On load we parse SKILL.md's
 * frontmatter and register it with the host skill registry, pointing the
 * resource base at the bundled directory so the model can resolve
 * `references/...` and `scripts/...` directly.
 */
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SKILL_DIR = join(HERE, '..', 'skills', 'hoi4-modding')
const SKILL_FILE = join(SKILL_DIR, 'SKILL.md')

const FALLBACK = {
  name: 'hoi4-modding',
  description:
    'Hearts of Iron IV (HOI4) 1.19.3 modding: create/edit/validate/install/debug mods (focus trees, events, decisions, ideas, characters, technologies, MIO, special projects, GUI, localisation, DDS).',
  whenToUse:
    'Use when the user asks to create, edit, fix, validate, install, publish, or debug an HOI4 mod, or asks about HOI4 scripting.',
}

export const name = 'hoi4-modding-skill'
export const inject = ['skills']

/** Parse the small YAML frontmatter block used by SKILL.md (name/description/whenToUse). */
export function parseFrontmatter(raw) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(raw)
  if (!match) return { meta: {}, body: raw }
  const meta = {}
  for (const line of match[1].split(/\r?\n/)) {
    const idx = line.indexOf(':')
    if (idx <= 0) continue
    const key = line.slice(0, idx).trim()
    let value = line.slice(idx + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    if (key) meta[key] = value
  }
  return { meta, body: raw.slice(match[0].length) }
}

/** Read the bundled skill and return a registration object for ctx.skills.register(). */
export function loadSkill() {
  let raw
  try {
    raw = readFileSync(SKILL_FILE, 'utf8')
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    throw new Error(`[dsh-hoi4-modding] cannot read bundled skill at ${SKILL_FILE}: ${reason}`)
  }
  const { meta, body } = parseFrontmatter(raw)
  const description = meta.description || FALLBACK.description
  const whenToUse = meta.whenToUse || FALLBACK.whenToUse
  return {
    name: meta.name || FALLBACK.name,
    description,
    whenToUse,
    content: body.trimStart(),
    source: 'bundled',
    provider: 'hoi4-modding',
    path: SKILL_FILE,
    resourceBase: { kind: 'directory', path: SKILL_DIR },
  }
}

export function apply(ctx) {
  const register = (target) => {
    if (typeof target?.skills?.register !== 'function') {
      target?.logger?.warn?.('[dsh-hoi4-modding] skill registry is unavailable; skill not registered')
      return
    }
    target.skills.register(loadSkill())
  }

  if (ctx?.skills?.register) {
    register(ctx)
  } else if (typeof ctx?.inject === 'function') {
    ctx.inject(['skills'], (injected) => register(injected))
  } else {
    register(ctx)
  }
}

export default { name, inject, apply }
