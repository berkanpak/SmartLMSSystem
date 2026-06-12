// ── State Management ──────────────────────────────────────────────────────────

const state = {
  currentView: 'home',
  sessionId: new URLSearchParams(window.location.search).get('session') || 'default',
  courses: [],
  sessions: [],
  selectedCourseId: null,
  selectedDocIds: new Set(),
  isThinking: false
};

// ── Router ────────────────────────────────────────────────────────────────────

const router = {
  navigate(view, params = {}) {
    state.currentView = view;
    renderApp();
    
    if (view === 'chat') {
      document.getElementById('floating-input').classList.remove('hidden');
      if (params.action) {
        handleAutoAction(params.action);
      }
      if (params.docIds) {
        params.docIds.forEach(id => state.selectedDocIds.add(id));
      }
    } else {
      document.getElementById('floating-input').classList.add('hidden');
    }
    
    if (view === 'course-detail' && params.courseId) {
      loadCourseDetail(params.courseId);
    }
  }
};

// ── Rendering ──────────────────────────────────────────────────────────────────

async function renderApp() {
  const main = document.getElementById('app-view');
  if (!main) return;
  
  const tplId = `tpl-${state.currentView === 'courses' ? 'home' : state.currentView}`;
  const tpl = document.getElementById(tplId);
  if (!tpl) return;
  
  main.innerHTML = '';
  main.appendChild(tpl.content.cloneNode(true));

  if (state.currentView === 'home' || state.currentView === 'courses') {
    renderCourses();
  } else if (state.currentView === 'chat') {
    loadHistory();
  }
}

async function renderCourses() {
  const grid = document.getElementById('course-grid');
  if (!grid) return;
  
  if (state.courses.length === 0) {
    await fetchCourses();
  }
  
  grid.innerHTML = state.courses.map(c => `
    <div class="bg-white border border-outline-variant rounded-xl p-6 hover:shadow-md transition-all group relative overflow-hidden cursor-pointer" onclick="router.navigate('course-detail', {courseId: ${c.id}})">
      <div class="absolute top-0 left-0 w-1.5 h-full bg-primary"></div>
      <div class="flex justify-between items-start mb-6">
        <div>
          <h3 class="text-xl font-bold">${escHtml(c.name)}</h3>
          <p class="text-sm text-on-surface-variant">LMS Course ID: ${c.id}</p>
        </div>
        <span class="material-symbols-outlined text-outline group-hover:text-primary">arrow_forward_ios</span>
      </div>
      <div class="h-2 w-full bg-surface-container rounded-full overflow-hidden">
        <div class="h-full bg-primary" style="width: ${Math.floor(Math.random() * 40) + 30}%"></div>
      </div>
    </div>
  `).join('');
}

async function loadCourseDetail(courseId) {
  state.selectedCourseId = courseId;
  const course = state.courses.find(c => c.id == courseId);
  if (!course) return;

  const titleEl = document.getElementById('course-title');
  const subEl = document.getElementById('course-subtitle');
  if (titleEl) titleEl.textContent = course.name;
  if (subEl) subEl.textContent = `ID: ${course.id}`;
  
  const matList = document.getElementById('material-list');
  if (!matList) return;
  matList.innerHTML = '<p class="text-on-surface-variant">Loading materials...</p>';
  
  // Update AI Summaries from history
  updateCourseSummaries(courseId);
  
  try {
    const res = await fetch(`/api/materials/${courseId}`);
    const materials = await res.json();
    state.currentMaterials = materials;
    renderMaterials();
  } catch (e) {
    matList.innerHTML = '<p class="text-red-500">Failed to load materials.</p>';
  }
}

function renderMaterials() {
  const matList = document.getElementById('material-list');
  if (!matList) return;
  
  matList.innerHTML = (state.currentMaterials || []).map(m => {
    const isSelected = state.selectedDocIds.has(m.id);
    return `
      <div class="flex items-center gap-4 p-4 bg-white border ${isSelected ? 'border-primary ring-2 ring-primary/20 shadow-lg' : 'border-outline-variant'} rounded-xl group cursor-pointer hover:border-primary transition-all" onclick="toggleMaterialSelection('${m.id}')">
        <div class="w-12 h-12 flex items-center justify-center ${isSelected ? 'bg-primary text-white' : 'bg-red-50 text-red-600'} rounded-lg transition-colors">
          <span class="material-symbols-outlined text-3xl">${isSelected ? 'check_circle' : 'picture_as_pdf'}</span>
        </div>
        <div class="flex-1">
          <h4 class="font-bold ${isSelected ? 'text-primary' : 'group-hover:text-primary'}">${escHtml(m.title)}</h4>
          <p class="text-xs text-on-surface-variant">${isSelected ? 'Selected for AI Chat' : 'Click to select'}</p>
        </div>
        <div class="p-2">
          <span class="material-symbols-outlined ${isSelected ? 'text-primary' : 'text-outline'}">smart_toy</span>
        </div>
      </div>
    `;
  }).join('');

  updateContinueButton();
}

function toggleMaterialSelection(docId) {
  if (state.selectedDocIds.has(docId)) {
    state.selectedDocIds.delete(docId);
  } else {
    state.selectedDocIds.add(docId);
  }
  renderMaterials();
}

function updateContinueButton() {
  let btn = document.getElementById('continue-ai-btn');
  if (state.selectedDocIds.size > 0) {
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'continue-ai-btn';
      btn.className = 'fixed bottom-8 right-8 bg-primary text-white px-8 py-4 rounded-full font-bold shadow-2xl hover:scale-105 active:scale-95 transition-all flex items-center gap-3 z-50 animate-in slide-in-from-bottom-4';
      btn.innerHTML = `<span class="material-symbols-outlined">auto_awesome</span> Continue with AI (${state.selectedDocIds.size} files)`;
      btn.onclick = () => {
        const docIds = Array.from(state.selectedDocIds);
        router.navigate('chat', { courseId: state.selectedCourseId, docIds: docIds });
      };
      document.body.appendChild(btn);
    } else {
      btn.innerHTML = `<span class="material-symbols-outlined">auto_awesome</span> Continue with AI (${state.selectedDocIds.size} files)`;
      btn.classList.remove('hidden');
    }
  } else if (btn) {
    btn.classList.add('hidden');
  }
}

async function updateCourseSummaries(courseId) {
  const summaryContainer = document.getElementById('course-summaries');
  if (!summaryContainer) return;
  
  try {
    const res = await fetch(`/api/sessions/${state.sessionId}`);
    if (!res.ok) return;
    const session = await res.json();
    
    const summaries = (session.turns || [])
      .filter(t => t.role === 'assistant' && t.blocks)
      .flatMap(t => t.blocks)
      .filter(b => b.type === 'summary');

    const h2 = summaryContainer.querySelector('h2');
    summaryContainer.innerHTML = '';
    if (h2) summaryContainer.appendChild(h2);

    if (summaries.length === 0) {
      const p = document.createElement('p');
      p.className = 'text-xs text-on-surface-variant p-4 bg-surface-container rounded-xl italic';
      p.textContent = 'No AI summaries generated yet. Start a chat to see insights here.';
      summaryContainer.appendChild(p);
      return;
    }

    summaries.slice(-3).reverse().forEach(sum => {
      const div = document.createElement('div');
      div.className = 'p-4 bg-white border border-outline-variant rounded-xl space-y-2 shadow-sm animate-in fade-in slide-in-from-left-4';
      div.innerHTML = `
        <h3 class="font-bold text-[10px] text-primary uppercase tracking-widest">${escHtml(sum.title || sum.heading || 'Summary')}</h3>
        <p class="text-xs text-on-surface-variant line-clamp-3 leading-relaxed">${escHtml(sum.content || (sum.sections && sum.sections[0]?.body) || sum.text || '')}</p>
      `;
      summaryContainer.appendChild(div);
    });
  } catch (e) {
    console.error('Failed to load summaries:', e);
  }
}

// ── AI & Chat ────────────────────────────────────────────────────────────────

async function submitPrompt(text, courseIds = [], docIds = []) {
  if (!text.trim()) return;
  
  if (state.currentView !== 'chat') {
    router.navigate('chat');
  }

  appendMessage('user', text);
  showThinking();
  
  try {
    const cIds = courseIds.length ? courseIds : (state.selectedCourseId ? [state.selectedCourseId] : []);
    const dIds = docIds.length ? docIds : Array.from(state.selectedDocIds);
    await fetch(`/api/prompt/${state.sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text, 
        course_ids: cIds,
        doc_ids: dIds
      }),
    });
  } catch (e) {
    appendMessage('ai', 'Sorry, I encountered an error connecting to the server.');
    hideThinking();
  }
}

function appendMessage(role, text, blocks = []) {
  const thread = document.getElementById('chat-thread');
  if (!thread) return;

  const msg = document.createElement('div');
  msg.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in duration-300 mb-6`;
  
  if (role === 'user') {
    msg.innerHTML = `
      <div class="max-w-2xl bg-primary text-white p-4 rounded-2xl rounded-tr-none shadow-md">
        <p class="text-sm md:text-base">${escHtml(text)}</p>
      </div>
    `;
  } else {
    msg.innerHTML = `
      <div class="max-w-3xl space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
            <span class="material-symbols-outlined text-primary text-sm">smart_toy</span>
          </div>
          <span class="text-xs font-bold text-primary">StudyFlow AI</span>
        </div>
        <div class="bg-white p-5 rounded-2xl rounded-tl-none border border-outline-variant shadow-sm text-on-surface">
          <div class="prose prose-sm max-w-none text-on-surface">${text ? `<p>${escHtml(text)}</p>` : ''}</div>
          <div class="ai-blocks mt-4 space-y-4"></div>
        </div>
      </div>
    `;
    const blocksContainer = msg.querySelector('.ai-blocks');
    (blocks || []).forEach(block => {
      const el = renderBlock(block);
      if (el) blocksContainer.appendChild(el);
    });
  }

  thread.appendChild(msg);
  thread.scrollTo({ top: thread.scrollHeight, behavior: 'smooth' });
}

function renderBlock(block) {
  switch (block.type) {
    case 'flashcard_set': return renderFlashcards(block);
    case 'quiz':          return renderQuiz(block);
    case 'exam':          return renderQuiz(block); // Reuse quiz for exam
    case 'summary':       return renderSummary(block);
    default:              return null;
  }
}

function renderFlashcards(block) {
  const container = document.createElement('div');
  const head = document.createElement('div');
  head.className = 'block-head';
  head.innerHTML = `<span class="material-symbols-outlined">cards</span> <span>Flashcards</span>`;
  container.appendChild(head);

  const grid = document.createElement('div');
  grid.className = 'card-grid';
  const cards = block.cards || [];
  cards.forEach(card => {
    const fc = document.createElement('div');
    fc.className = 'flashcard';
    fc.innerHTML = `
      <div class="flashcard-inner">
        <div class="face">
          <div class="text-[10px] font-bold text-primary mb-2 uppercase tracking-wider">${escHtml(card.tag || 'Concept')}</div>
          <div class="font-medium text-sm">${escHtml(card.front)}</div>
        </div>
        <div class="face back">
          <div class="text-[10px] font-bold text-tertiary mb-2 uppercase tracking-wider">Answer</div>
          <div class="text-xs leading-relaxed">${escHtml(card.back)}</div>
        </div>
      </div>
    `;
    fc.onclick = () => fc.classList.toggle('flipped');
    grid.appendChild(fc);
  });
  container.appendChild(grid);
  return container;
}

function renderQuiz(block) {
  const container = document.createElement('div');
  const head = document.createElement('div');
  head.className = 'block-head';
  head.innerHTML = `<span class="material-symbols-outlined">quiz</span> <span>${block.type === 'exam' ? 'Practice Exam' : 'Quiz'}</span>`;
  container.appendChild(head);

  const questions = block.questions || [];
  questions.forEach((q, i) => {
    const card = document.createElement('div');
    card.className = 'qcard shadow-sm border border-outline-variant';
    
    const options = q.options || ['True', 'False'];
    const correctIdx = q.correct !== undefined ? q.correct : (q.answer === true ? 0 : 1);

    const optionsHtml = options.map((opt, idx) => `
      <div class="opt flex justify-between items-center group" data-idx="${idx}">
        <span class="text-sm">${escHtml(opt)}</span>
        <span class="material-symbols-outlined hidden group-[.correct]:block text-green-500">check_circle</span>
        <span class="material-symbols-outlined hidden group-[.wrong]:block text-red-500">cancel</span>
      </div>
    `).join('');

    card.innerHTML = `
      <div class="text-[10px] font-bold text-outline mb-1 uppercase tracking-wider">Question ${i + 1}</div>
      <div class="font-bold mb-4 text-on-surface">${escHtml(q.text || q.question)}</div>
      <div class="opts-container">${optionsHtml}</div>
      <div class="explanation hidden mt-4 p-3 bg-blue-50 rounded-lg text-xs text-blue-800 border border-blue-100">
        <strong>Explanation:</strong> ${escHtml(q.explanation || 'Based on source material.')}
      </div>
    `;

    card.querySelectorAll('.opt').forEach(optEl => {
      optEl.onclick = () => {
        if (card.classList.contains('answered')) return;
        card.classList.add('answered');
        const selectedIdx = parseInt(optEl.dataset.idx);
        if (selectedIdx === correctIdx) {
          optEl.classList.add('correct');
        } else {
          optEl.classList.add('wrong');
          card.querySelector(`[data-idx="${correctIdx}"]`).classList.add('correct');
        }
        card.querySelector('.explanation').classList.remove('hidden');
      };
    });
    container.appendChild(card);
  });
  return container;
}

function renderSummary(block) {
  const container = document.createElement('div');
  const head = document.createElement('div');
  head.className = 'block-head';
  head.innerHTML = `<span class="material-symbols-outlined">article</span> <span>Summary</span>`;
  container.appendChild(head);

  const div = document.createElement('div');
  div.className = 'summary-block shadow-sm border border-outline-variant';
  const sections = block.sections || (block.content ? [{title: 'Key Points', body: block.content}] : []);
  div.innerHTML = `
    <h3 class="text-sm font-bold text-primary mb-3">${escHtml(block.heading || block.title || 'Overview')}</h3>
    <div class="space-y-4">
      ${sections.map(sec => `
        <div>
          <div class="sec-title flex items-center gap-2 font-bold text-on-surface text-xs">
            <span class="w-1.5 h-1.5 rounded-full bg-primary"></span>
            ${escHtml(sec.title)}
          </div>
          <div class="sec-body pl-3.5 text-xs text-on-surface-variant leading-relaxed">${escHtml(sec.body || sec.content)}</div>
        </div>
      `).join('')}
    </div>
  `;
  container.appendChild(div);
  return container;
}

// ── SSE & History ─────────────────────────────────────────────────────────────

function connectSSE() {
  if (window.eventSource) window.eventSource.close();
  const es = new EventSource(`/api/events/${state.sessionId}`);
  window.eventSource = es;
  es.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'blocks') {
        hideThinking();
        appendMessage('ai', '', msg.blocks);
      }
    } catch (_) {}
  };
  es.onerror = () => setTimeout(connectSSE, 3000);
}

async function loadHistory() {
  if (!state.sessionId || state.sessionId === 'default') return;
  const res = await fetch(`/api/sessions/${state.sessionId}`);
  if (!res.ok) return;
  const session = await res.json();
  const thread = document.getElementById('chat-thread');
  if (!thread) return;
  thread.innerHTML = '';
  (session.turns || []).forEach(turn => {
    appendMessage(turn.role, turn.text, turn.blocks || []);
  });
}

// ── API Helpers ────────────────────────────────────────────────────────────────

async function fetchCourses() {
  const res = await fetch('/api/courses');
  state.courses = await res.json();
}

async function loadSessions() {
  const res = await fetch('/api/sessions');
  state.sessions = await res.json();
  const nav = document.getElementById('session-history');
  if (!nav) return;
  nav.innerHTML = state.sessions.slice(0, 5).map(s => `
    <button class="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-surface-container-low transition-all text-left truncate ${state.sessionId === s.id ? 'bg-surface-container' : ''}" onclick="state.sessionId = '${s.id}'; connectSSE(); router.navigate('chat')">
      <span class="material-symbols-outlined text-outline text-xs">history</span>
      <span class="text-[11px] font-medium truncate">${escHtml(s.title)}</span>
    </button>
  `).join('');
}

function handleAutoAction(action) {
  const course = state.courses[0];
  if (!course) return;
  const prompts = {
    'quiz': `Prepare a quiz for ${course.name}.`,
    'summary': `Summarize the course ${course.name}.`
  };
  if (prompts[action]) submitPrompt(prompts[action], [course.id]);
}

function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showThinking() {
  const thread = document.getElementById('chat-thread');
  if (!thread) return;
  const div = document.createElement('div');
  div.id = 'thinking-indicator';
  div.className = 'flex justify-start mb-6';
  div.innerHTML = `<div class="bg-indigo-50 px-4 py-2 rounded-full text-[10px] text-primary animate-pulse">AI is thinking...</div>`;
  thread.appendChild(div);
  thread.scrollTo({ top: thread.scrollHeight, behavior: 'smooth' });
}

function hideThinking() {
  const el = document.getElementById('thinking-indicator');
  if (el) el.remove();
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', async () => {
  await fetchCourses();
  await loadSessions();
  
  const urlParams = new URLSearchParams(window.location.search);
  let sid = urlParams.get('session');

  if (!sid || sid === 'default') {
    if (state.sessions.length > 0) {
      sid = state.sessions[0].id;
    } else {
      try {
        const res = await fetch('/api/sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: 'New Study Session' })
        });
        const data = await res.json();
        sid = data.id;
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('session', sid);
        window.history.pushState({}, '', newUrl);
      } catch (e) {
        sid = 'default';
      }
    }
  }

  state.sessionId = sid;
  renderApp();
  connectSSE();
  
  document.getElementById('send-btn').onclick = () => {
    const input = document.getElementById('main-prompt');
    submitPrompt(input.value);
    input.value = '';
  };
  
  document.getElementById('main-prompt').onkeydown = (e) => {
    if (e.key === 'Enter') {
      document.getElementById('send-btn').click();
    }
  };
});