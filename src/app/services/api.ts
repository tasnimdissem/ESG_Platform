export type NewsItem = {
  id: number;
  title: string;
  source: string;
  region: string;
  category: string;
  date: string;
};

export type ChatResponse = {
  answer: string;
  sources: string[];
  confidence: number;
  isFallback?: boolean;
};

export type TranscribeResponse = {
  transcript: string;
  command: string;
  query: string;
  language_hint: string | null;
  supported_languages: string[];
};

export type VoiceQueryResponse = {
  transcript: string;
  command: string;
  query: string;
  answer: string;
  sources: string[];
  confidence: number;
  session_id: string | null;
};

export type ConversationTurn = {
  question: string;
  answer: string;
  timestamp: string;
};

export type ConversationHistoryResponse = {
  session_id: string;
  history: ConversationTurn[];
  turn_count: number;
};

export type RecommendationItem = {
  id: string;
  title: string;
  category: 'Environmental' | 'Social' | 'Governance';
  priority: 'high' | 'medium' | 'low';
  impact: number;
  effort: 'low' | 'medium' | 'high';
  timeline: string;
  currentScore: number;
  targetScore: number;
  description: string;
  actions: string[];
  status: 'not-started' | 'in-progress' | 'completed';
};

export type RecommendationsResponse = {
  focus_area: string;
  risk_level: string;
  recommendations: RecommendationItem[];
  sources: string[];
  rag_used: boolean;
  source_count: number;
  confidence: number;
};

type IntegrationRequest = {
  client_request_id?: string;
  message: string;
  top_k?: number;
  include_recommendations?: boolean;
  signals?: Record<string, unknown>;
  filters?: Record<string, unknown>;
};

type IntegrationRequestEcho = {
  request_id?: string;
  question?: string;
  top_k?: number;
  include_recommendations?: boolean;
  signals?: Record<string, unknown>;
  filters?: Record<string, unknown>;
};

type IntegrationSource = {
  rank?: number;
  source_type?: string;
  source_name?: string;
  chunk_id?: string;
  text?: string;
  distance?: number;
  confidence?: number;
};

type IntegrationRecommendation = {
  id?: string;
  title?: string;
  pillar?: string;
  impact?: number | string;
  effort?: string;
  timeline?: string;
  priority?: number | string;
  justification?: string;
  sources?: Array<Record<string, unknown>>;
};

type IntegrationResponse = {
  request?: IntegrationRequestEcho;
  response?: {
    answer?: string;
    recommendations?: IntegrationRecommendation[];
    sources?: IntegrationSource[];
    confidence?: number;
  };
  meta?: {
    service?: string;
    version?: string;
    timestamp?: string;
    source?: string;
  };
};

export type CompanyHistoryItem = {
  date: string;
  indicateurs: Record<string, unknown>;
  scores: {
    E: number | null;
    S: number | null;
    G: number | null;
    global: number | null;
  };
};

export type CompanyRecord = {
  entreprise_id: string;
  nom: string;
  sector?: string | null;
  country?: string | null;
  historique: CompanyHistoryItem[];
  created_by_user_id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CompanyCreatePayload = {
  name: string;
  sector?: string | null;
  country?: string | null;
  indicators?: Record<string, unknown>;
  score?: number;
};

export type CompanyUpdatePayload = {
  name?: string;
  sector?: string | null;
  country?: string | null;
};

export type CompanyHistoryPayload = {
  indicators: Record<string, unknown>;
  score: number;
};


type RecommendationsQuery = {
  score?: number;
  risk_level?: string;
  focus_area?: string;
} & Record<string, unknown>;

export type PredictionPayload = {
  co2_emissions: number;
  revenue: number;
  governance_score: number;
  social_score: number;
  environment_score: number;
};

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    credentials: 'include',
    ...init,
  });

  if (!response.ok) {
    const rawError = await response.text();

    let errorMessage = rawError || `Requête échouée avec le statut ${response.status}`;
    try {
      const parsed = JSON.parse(rawError) as { error?: string; message?: string };
      errorMessage = parsed.error ?? parsed.message ?? errorMessage;
    } catch {
      // Conserver le message brut lorsque la réponse n'est pas du JSON.
    }

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

async function fetchIntegration(payload: IntegrationRequest): Promise<IntegrationResponse> {
  return fetchJson<IntegrationResponse>('/api/v1/integration', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

function normalizeSourceLabels(sources: IntegrationSource[] | undefined): string[] {
  if (!Array.isArray(sources)) return [];
  return sources
    .map((source, index) => {
      const label = source.source_name ?? source.chunk_id ?? source.source_type;
      return (label && String(label).trim()) || `Source ${index + 1}`;
    })
    .filter(Boolean);
}

function normalizePriority(value: unknown): 'high' | 'medium' | 'low' {
  if (typeof value === 'number') {
    if (value >= 4) return 'high';
    if (value <= 2) return 'low';
    return 'medium';
  }

  const normalized = String(value ?? '').toLowerCase();
  if (normalized === 'high') return 'high';
  if (normalized === 'low') return 'low';
  return 'medium';
}

function normalizeImpact(value: unknown): number {
  if (typeof value === 'number') return value;
  const normalized = String(value ?? '').toLowerCase();
  if (normalized === 'high') return 12;
  if (normalized === 'medium') return 8;
  if (normalized === 'low') return 5;
  return 8;
}

function normalizeCategory(value: unknown): 'Environmental' | 'Social' | 'Governance' {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized.startsWith('social')) return 'Social';
  if (normalized.startsWith('governance')) return 'Governance';
  return 'Environmental';
}

function normalizeRecommendationItems(items: IntegrationRecommendation[] | undefined): RecommendationItem[] {
  if (!Array.isArray(items)) return [];

  return items.map((item, index) => {
    const category = normalizeCategory(item.pillar);
    const priority = normalizePriority(item.priority);
    const impact = normalizeImpact(item.impact);

    const rawEffort = String(item.effort ?? 'medium').toLowerCase();
    const effort: 'low' | 'medium' | 'high' = rawEffort === 'high' ? 'high' : rawEffort === 'low' ? 'low' : 'medium';

    return {
      id: String(item.id ?? `rec-${index + 1}`),
      title: String(item.title ?? `Recommendation ${index + 1}`),
      category,
      priority,
      impact,
      effort,
      timeline: String(item.timeline ?? '3 months'),
      currentScore: 70,
      targetScore: 82,
      description: String(item.justification ?? item.title ?? 'No description provided.'),
      actions: [String(item.justification ?? item.title ?? 'Review this recommendation.')],
      status: 'not-started',
    };
  });
}

export async function fetchChatResponse(message: string): Promise<ChatResponse> {
  const data = await fetchIntegration({
    client_request_id: `chat-${Date.now()}`,
    message,
    top_k: 5,
    include_recommendations: false,
  });

  return {
    answer: data.response?.answer ?? '',
    sources: normalizeSourceLabels(data.response?.sources),
    confidence: data.response?.sources?.length ? 0.9 : 0,
    isFallback: data.meta?.source === 'fallback', // FIXED: Mapper la source du meta
  };
}

export async function fetchRecommendations(payload: RecommendationsQuery = {}): Promise<RecommendationsResponse> {
  const data = await fetchIntegration({
    client_request_id: `recommend-${Date.now()}`,
    message: 'Provide prioritized ESG recommendations from the available context.',
    top_k: 5,
    include_recommendations: true,
    signals: {
      esg_score: payload.score,
      risk_level: payload.risk_level,
      focus_area: payload.focus_area,
    },
  });

  const recommendations = normalizeRecommendationItems(data.response?.recommendations);
  const sources = normalizeSourceLabels(data.response?.sources);

  return {
    focus_area: String(payload.focus_area ?? 'overall'),
    risk_level: String(payload.risk_level ?? 'Medium'),
    recommendations,
    sources,
    rag_used: sources.length > 0,
    source_count: sources.length,
    confidence: Number(data.response?.confidence ?? 0),
  };
}

export async function fetchLegacyRecommendations(payload: RecommendationsQuery = {}): Promise<RecommendationsResponse> {
  return fetchRecommendations(payload);
}

export async function fetchPrediction(payload: PredictionPayload) {
  return fetchJson('/api/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchNewsItems(limit = 8): Promise<NewsItem[]> {
  const data = await fetchJson<{ items?: NewsItem[] }>(`/api/news?limit=${limit}`);
  return Array.isArray(data.items) ? data.items : [];
}

export async function fetchCompanies(): Promise<CompanyRecord[]> {
  return fetchJson<CompanyRecord[]>('/api/companies');
}

export async function fetchCompany(companyId: string): Promise<CompanyRecord> {
  return fetchJson<CompanyRecord>(`/api/companies/${companyId}`);
}

export async function createCompany(payload: CompanyCreatePayload): Promise<CompanyRecord> {
  return fetchJson<CompanyRecord>('/api/companies', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateCompany(companyId: string, payload: CompanyUpdatePayload): Promise<CompanyRecord> {
  return fetchJson<CompanyRecord>(`/api/companies/${companyId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deleteCompany(companyId: string): Promise<void> {
  await fetchJson<{ message: string }>(`/api/companies/${companyId}`, {
    method: 'DELETE',
  });
}

export async function addCompanyHistory(companyId: string, payload: CompanyHistoryPayload): Promise<CompanyRecord> {
  return fetchJson<CompanyRecord>(`/api/companies/${companyId}/history`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Voice & conversation API
// ---------------------------------------------------------------------------

async function fetchMultipart<T>(url: string, body: FormData): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    body,
  });
  if (!response.ok) {
    const raw = await response.text();
    let msg = raw || `Request failed with status ${response.status}`;
    try {
      const parsed = JSON.parse(raw) as { error?: string };
      msg = parsed.error ?? msg;
    } catch { /* keep raw */ }
    throw new Error(msg);
  }
  return (await response.json()) as T;
}

export async function transcribeAudio(
  audio: Blob | File,
  language = 'auto'
): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append('audio', audio, audio instanceof File ? audio.name : 'recording.webm');
  form.append('language', language);
  return fetchMultipart<TranscribeResponse>('/api/v1/transcribe', form);
}

export async function sendVoiceQuery(
  audioOrBlob: Blob | File | null,
  sessionId: string | null,
  language = 'auto',
  topK = 5,
  fallbackText?: string
): Promise<VoiceQueryResponse> {
  const form = new FormData();
  const cleanText = fallbackText?.trim() ?? '';
  const hasAudio = audioOrBlob !== null && audioOrBlob.size > 0;

  if (cleanText) {
    // Browser already transcribed via Web Speech API — send as text, skip Whisper
    form.append('text', cleanText);
  } else if (hasAudio) {
    // No browser transcript — send raw audio for Whisper to transcribe
    form.append('audio', audioOrBlob as Blob | File, audioOrBlob instanceof File ? audioOrBlob.name : 'recording.webm');
  } else {
    throw new Error('No audio or text to send');
  }
  if (sessionId) form.append('session_id', sessionId);
  form.append('language', language);
  form.append('top_k', String(topK));
  return fetchMultipart<VoiceQueryResponse>('/api/v1/voice-query', form);
}

export async function fetchChatResponseWithSession(
  message: string,
  sessionId: string | null
): Promise<ChatResponse> {
  const payload: IntegrationRequest & { session_id?: string } = {
    client_request_id: `chat-${Date.now()}`,
    message,
    top_k: 5,
    include_recommendations: false,
  };
  if (sessionId) payload.session_id = sessionId;
  const data = await fetchIntegration(payload);

  return {
    answer: data.response?.answer ?? '',
    sources: normalizeSourceLabels(data.response?.sources),
    confidence: data.response?.sources?.length ? 0.9 : 0,
    isFallback: data.meta?.source === 'fallback',
  };
}

export async function getConversationHistory(sessionId: string): Promise<ConversationHistoryResponse> {
  return fetchJson<ConversationHistoryResponse>(`/api/v1/conversations/${sessionId}`);
}

export async function clearConversationHistory(sessionId: string): Promise<void> {
  await fetchJson<{ cleared: boolean }>(`/api/v1/conversations/${sessionId}`, {
    method: 'DELETE',
  });
}

// ---------------------------------------------------------------------------
// Persistent chat history (per user account)
// ---------------------------------------------------------------------------

export type ChatConversationSummary = {
  id: number;
  title: string;
  session_id: string | null;
  created_at: string;
};

export type ChatMessageRecord = {
  id: number;
  sender: 'user' | 'bot';
  text: string;
  sources: string[];
  timestamp: string;
};

export type ChatConversationDetail = {
  conversation: ChatConversationSummary;
  messages: ChatMessageRecord[];
};

export async function listChatConversations(): Promise<ChatConversationSummary[]> {
  return fetchJson<ChatConversationSummary[]>('/api/chat/conversations');
}

export async function createChatConversation(
  title = 'Nouvelle conversation',
  sessionId?: string
): Promise<ChatConversationSummary> {
  return fetchJson<ChatConversationSummary>('/api/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ title, session_id: sessionId }),
  });
}

export async function getChatConversation(convId: number): Promise<ChatConversationDetail> {
  return fetchJson<ChatConversationDetail>(`/api/chat/conversations/${convId}`);
}

export async function saveChatMessage(
  convId: number,
  sender: 'user' | 'bot',
  text: string,
  sources: string[] = []
): Promise<ChatMessageRecord> {
  return fetchJson<ChatMessageRecord>(`/api/chat/conversations/${convId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ sender, text, sources }),
  });
}

export async function deleteChatConversation(convId: number): Promise<void> {
  await fetchJson<{ deleted: boolean }>(`/api/chat/conversations/${convId}`, {
    method: 'DELETE',
  });
}
