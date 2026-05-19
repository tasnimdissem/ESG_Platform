import { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Upload, X, Globe } from 'lucide-react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

export type VoiceLanguage = 'auto' | 'fr' | 'en' | 'es' | 'de' | 'ar' | 'zh' | 'pt';

const LANGUAGE_LABELS: Record<VoiceLanguage, string> = {
  auto: 'Auto-detect',
  fr: 'Français',
  en: 'English',
  es: 'Español',
  de: 'Deutsch',
  ar: 'العربية',
  zh: '中文',
  pt: 'Português',
};

// Map voice language codes to Web Speech API BCP-47 locales
const WEB_SPEECH_LOCALE: Record<VoiceLanguage, string> = {
  auto: 'fr-FR',
  fr: 'fr-FR',
  en: 'en-US',
  es: 'es-ES',
  de: 'de-DE',
  ar: 'ar-SA',
  zh: 'zh-CN',
  pt: 'pt-BR',
};

interface VoiceRecorderProps {
  onResult: (transcript: string, audioBlob: Blob | null) => void;
  onInterim?: (text: string) => void;
  disabled?: boolean;
  language: VoiceLanguage;
  onLanguageChange: (lang: VoiceLanguage) => void;
}

export default function VoiceRecorder({
  onResult,
  onInterim,
  disabled = false,
  language,
  onLanguageChange,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Refs so the onstop closure always reads the latest transcript values
  const transcriptRef = useRef<string>('');
  const interimRef = useRef<string>('');

  const locale = WEB_SPEECH_LOCALE[language];
  const { isListening, transcript, interimTranscript, isSupported, startListening, stopListening, resetTranscript } =
    useSpeechRecognition(locale);

  // Keep refs in sync so the onstop closure always reads latest values
  useEffect(() => { transcriptRef.current = transcript; }, [transcript]);
  useEffect(() => { interimRef.current = interimTranscript; }, [interimTranscript]);

  // Forward interim results to parent
  useEffect(() => {
    if (interimTranscript && onInterim) onInterim(interimTranscript);
  }, [interimTranscript, onInterim]);

  const startRecording = useCallback(async () => {
    setUploadError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const mediaRecorder = new MediaRecorder(stream, { mimeType });

      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        // Read from refs — not closed-over state — so we get the latest transcript
        const finalText = (transcriptRef.current + ' ' + interimRef.current).trim();
        if (audioBlob.size > 0) {
          onResult(finalText, audioBlob);
        } else if (finalText) {
          // Audio capture produced 0 bytes (e.g. stopped immediately); send transcript only
          onResult(finalText, null);
        }
        resetTranscript();
      };

      mediaRecorder.start(200);
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      startListening();
    } catch {
      setUploadError('Microphone access denied');
    }
  }, [onResult, resetTranscript, startListening]);

  const stopRecording = useCallback(() => {
    stopListening();
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    setIsRecording(false);
  }, [stopListening]);

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setUploadError(null);
      const file = e.target.files?.[0];
      if (!file) return;

      const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
      const allowed = ['mp3', 'wav', 'm4a', 'webm', 'ogg', 'flac', 'mp4', 'mpeg'];
      if (!allowed.includes(ext)) {
        setUploadError(`Unsupported format (.${ext}). Use: ${allowed.join(', ')}`);
        return;
      }
      if (file.size > 25 * 1024 * 1024) {
        setUploadError('File exceeds 25 MB limit');
        return;
      }
      onResult('', file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    },
    [onResult]
  );

  const isActive = isRecording || isListening;
  const liveText = transcript + (interimTranscript ? ` ${interimTranscript}` : '');

  return (
    <div className="flex flex-col gap-2">
      {/* Controls row */}
      <div className="flex items-center gap-2">
        {/* Mic button */}
        <button
          type="button"
          disabled={disabled}
          onClick={isActive ? stopRecording : startRecording}
          title={isActive ? 'Stop recording' : 'Start voice input'}
          className={`relative flex items-center justify-center w-10 h-10 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-offset-1
            ${disabled ? 'opacity-40 cursor-not-allowed bg-gray-200' : isActive
              ? 'bg-red-500 hover:bg-red-600 focus:ring-red-400 shadow-lg'
              : 'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-400'}`}
        >
          {isActive ? (
            <MicOff className="w-4 h-4 text-white" />
          ) : (
            <Mic className="w-4 h-4 text-white" />
          )}
          {isActive && (
            <span className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-40" />
          )}
        </button>

        {/* File upload button */}
        <label
          title="Upload audio file (.mp3, .wav, …)"
          className={`flex items-center justify-center w-10 h-10 rounded-full cursor-pointer transition-all
            ${disabled ? 'opacity-40 cursor-not-allowed bg-gray-200' : 'bg-gray-100 hover:bg-gray-200 border border-gray-300'}`}
        >
          <Upload className="w-4 h-4 text-gray-600" />
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp3,.wav,.m4a,.webm,.ogg,.flac,.mp4,.mpeg"
            className="sr-only"
            disabled={disabled}
            onChange={handleFileUpload}
          />
        </label>

        {/* Language selector */}
        <div className="relative">
          <button
            type="button"
            disabled={disabled}
            onClick={() => setShowLangMenu((v) => !v)}
            title="Select language"
            className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium bg-gray-100 hover:bg-gray-200 border border-gray-300 transition-all disabled:opacity-40"
          >
            <Globe className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-gray-700">{LANGUAGE_LABELS[language]}</span>
          </button>
          {showLangMenu && (
            <div className="absolute bottom-full mb-1 left-0 z-20 bg-white border border-gray-200 rounded-lg shadow-lg min-w-[140px] py-1">
              {(Object.keys(LANGUAGE_LABELS) as VoiceLanguage[]).map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => {
                    onLanguageChange(lang);
                    setShowLangMenu(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs hover:bg-emerald-50 transition-colors
                    ${language === lang ? 'text-emerald-700 font-semibold bg-emerald-50' : 'text-gray-700'}`}
                >
                  {LANGUAGE_LABELS[lang]}
                </button>
              ))}
            </div>
          )}
        </div>

        {!isSupported && (
          <span className="text-xs text-amber-600">Live transcript unavailable in this browser</span>
        )}
      </div>

      {/* Real-time transcript bubble */}
      {isActive && (
        <div className="px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-sm text-gray-800 min-h-[36px]">
          {liveText ? (
            <>
              <span className="text-gray-900">{transcript}</span>
              {interimTranscript && (
                <span className="text-gray-400 italic"> {interimTranscript}</span>
              )}
            </>
          ) : (
            <span className="text-gray-400 italic animate-pulse">Listening…</span>
          )}
        </div>
      )}

      {/* Upload error */}
      {uploadError && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          <X className="w-3 h-3 flex-shrink-0" />
          {uploadError}
        </div>
      )}
    </div>
  );
}
