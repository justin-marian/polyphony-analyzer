const fs = require('fs');
const path = require('path');
const base = '/mnt/data';
const out = path.join(base, 'data');
fs.mkdirSync(out, {recursive: true});

const nameMap = {
  session_hh1: 'Human-Human 1 (Creativity)',
  session_hh2: 'Human-Human 2 (Ethics)',
  session_hc1: 'Human-Chatbot 1 (AGI)',
  session_hc2: 'Human-Chatbot 2 (Consciousness)',
  session_cc1: 'Chatbot-Chatbot 1 (Creativity)',
  session_cc2: 'Chatbot-Chatbot 2 (AGI)'
};
const typeMap = {
  session_hh1: 'human-human',
  session_hh2: 'human-human',
  session_hc1: 'human-chatbot',
  session_hc2: 'human-chatbot',
  session_cc1: 'chatbot-chatbot',
  session_cc2: 'chatbot-chatbot'
};

const sessions = [];
fs.readdirSync(base).filter(f => /^session_.*\.txt$/.test(f)).sort().forEach(file => {
  const sid = file.replace(/\.txt$/, '');
  const lines = fs.readFileSync(path.join(base, file), 'utf8').split(/\r?\n/);
  let header = '', topic = '', personas = [];
  const utterances = [];

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith('#')) {
      header = line.replace(/^#\s*/, '');
      const m = header.match(/topic:\s*(.*?)(?:\s*\(Personas:\s*"(.*?)"\s*vs\.\s*"(.*?)"\)|$)/);
      if (m) {
        topic = m[1].trim();
        if (m[2] && m[3]) personas = [m[2], m[3]];
      }
      continue;
    }
  
    const m = line.match(/^([A-Za-z0-9_\-. ]+?)\s*:\s*(.+)$/);
    if (m) {
      utterances.push({
        index: utterances.length,
        speaker: m[1].trim(),
        text: m[2].trim(),
        reply_to: null
      });
    }
  }

  const participants = [];
  utterances.forEach(u => { if (!participants.includes(u.speaker)) participants.push(u.speaker); });
  if (!personas.length) personas = participants.slice();
  const data = {
    id: sid,
    name: nameMap[sid] || sid,
    type: typeMap[sid] || 'unknown',
    topic,
    personas,
    source_file: file,
    utterance_count: utterances.length,
    participants,
    utterances,
    text: utterances.map(u => `${u.speaker}: ${u.text}`).join('\n')
  };

  fs.writeFileSync(path.join(out, `${sid}.json`), JSON.stringify(data, null, 2), 'utf8');
  sessions.push(data);
});

const index = sessions.map(s => ({
  id: s.id,
  name: s.name,
  type: s.type,
  topic: s.topic,
  participants: s.participants,
  utterance_count: s.utterance_count
}));
fs.writeFileSync(path.join(out, 'sessions_index.json'), JSON.stringify(index, null, 2), 'utf8');
fs.writeFileSync(path.join(out, 'sessions_all.json'), JSON.stringify({sessions}, null, 2), 'utf8');
console.log(`Created ${sessions.length} JSON sessions in ${out}`);
