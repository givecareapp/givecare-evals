#!/usr/bin/env npx tsx
/**
 * Convert promptfoo YAML eval datasets to HuggingFace JSONL format.
 *
 * Usage: npx tsx scripts/convert-yaml-to-jsonl.ts
 *
 * Reads from the givecare monorepo evals package, outputs to data/.
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, join } from 'node:path'
import { parse } from 'yaml'

const EVALS_DIR = resolve(__dirname, '../../../givecare/packages/evals/src/datasets')
const OUT_DIR = resolve(__dirname, '../data')

interface PromptfooTest {
  description: string
  vars: { input: string }
  providers?: unknown[]
  assert: Array<{
    type: string
    value: string | string[]
  }>
}

interface EvalRecord {
  id: string
  split: string
  category: string
  subcategory: string
  input: string
  expected_behaviors: string[]
  forbidden_patterns: string[]
  source?: string
}

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

function extractCategory(desc: string): { category: string; subcategory: string } {
  const match = desc.match(/^([^:]+):\s*(.+)$/)
  if (match) return { category: slugify(match[1]), subcategory: match[2].trim() }
  return { category: 'general', subcategory: desc }
}

function extractBehaviors(asserts: PromptfooTest['assert']): {
  expected: string[]
  forbidden: string[]
} {
  const expected: string[] = []
  const forbidden: string[] = []

  for (const a of asserts) {
    if (a.type === 'llm-rubric' && typeof a.value === 'string') {
      expected.push(a.value)
    } else if (a.type === 'contains-any' || a.type === 'icontains-any' || a.type === 'icontains') {
      const vals = Array.isArray(a.value) ? a.value : [a.value]
      expected.push(`Response should reference: ${vals.join(', ')}`)
    } else if (a.type === 'not-contains-any' || a.type === 'not-contains') {
      const vals = Array.isArray(a.value) ? a.value : [a.value]
      forbidden.push(...vals)
    }
  }

  return { expected, forbidden }
}

function convertFile(
  filename: string,
  split: string,
  sourceNote?: string
): EvalRecord[] {
  const raw = readFileSync(join(EVALS_DIR, filename), 'utf-8')
  const tests: PromptfooTest[] = parse(raw)
  const records: EvalRecord[] = []

  for (let i = 0; i < tests.length; i++) {
    const t = tests[i]
    const { category, subcategory } = extractCategory(t.description)
    const { expected, forbidden } = extractBehaviors(t.assert)

    const record: EvalRecord = {
      id: `${split}-${String(i + 1).padStart(3, '0')}`,
      split,
      category,
      subcategory,
      input: t.vars.input,
      expected_behaviors: expected,
      forbidden_patterns: forbidden,
    }

    if (sourceNote) record.source = sourceNote

    records.push(record)
  }

  return records
}

// Convert each dataset
const coreBehaviors = convertFile('core-behaviors.yaml', 'core-behaviors')
const redTeam = convertFile('red-team.yaml', 'red-team')
const reddit = convertFile(
  'reddit-caregivers.yaml',
  'reddit-caregivers',
  'Curated from public posts on r/CaregiverSupport, r/AgingParents, r/dementia, r/Alzheimers. Adapted to SMS-length format.'
)
const multiTurn = convertFile('multi-turn.yaml', 'multi-turn')

function writeJsonl(filename: string, records: EvalRecord[]) {
  const lines = records.map(r => JSON.stringify(r)).join('\n') + '\n'
  writeFileSync(join(OUT_DIR, filename), lines)
  console.log(`  ${filename}: ${records.length} records`)
}

console.log('Converting datasets to JSONL...\n')
writeJsonl('core-behaviors.jsonl', coreBehaviors)
writeJsonl('red-team.jsonl', redTeam)
writeJsonl('reddit-caregivers.jsonl', reddit)
writeJsonl('multi-turn.jsonl', multiTurn)

// Combined file
const all = [...coreBehaviors, ...redTeam, ...reddit, ...multiTurn]
writeJsonl('all.jsonl', all)

console.log(`\nTotal: ${all.length} records`)
