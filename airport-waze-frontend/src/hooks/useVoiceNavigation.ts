/**
 * Voice Navigation Hook for AirportWaze
 * Provides speech synthesis for turn-by-turn directions and voice command recognition
 * Supports multi-language and hands-free navigation mode
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// Types
interface VoiceNavigationOptions {
  language?: string;
  autoSpeak?: boolean;
  voiceCommandsEnabled?: boolean;
  volume?: number;
  rate?: number;
  pitch?: number;
}

interface NavigationInstruction {
  text: string;
  distance?: number;
  direction?: 'forward' | 'left' | 'right' | 'backward' | 'up' | 'down';
  priority?: 'low' | 'normal' | 'high';
}

interface VoiceCommand {
  command: string;
  action: string;
  parameters?: Record<string, any>;
}

interface VoiceNavigationState {
  isSupported: boolean;
  isSpeaking: boolean;
  isListening: boolean;
  lastSpoken: string | null;
  lastCommand: VoiceCommand | null;
  error: string | null;
  availableVoices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
}

// Language configurations
const LANGUAGE_CONFIGS: Record<string, { code: string; voicePattern: RegExp }> = {
  'en-US': { code: 'en-US', voicePattern: /en[-_]US|english.*united.*states/i },
  'en-GB': { code: 'en-GB', voicePattern: /en[-_]GB|english.*uk|english.*british/i },
  'es-ES': { code: 'es-ES', voicePattern: /es[-_]ES|spanish.*spain/i },
  'es-MX': { code: 'es-MX', voicePattern: /es[-_]MX|spanish.*mexico/i },
  'fr-FR': { code: 'fr-FR', voicePattern: /fr[-_]FR|french.*france/i },
  'de-DE': { code: 'de-DE', voicePattern: /de[-_]DE|german/i },
  'it-IT': { code: 'it-IT', voicePattern: /it[-_]IT|italian/i },
  'pt-BR': { code: 'pt-BR', voicePattern: /pt[-_]BR|portuguese.*brazil/i },
  'zh-CN': { code: 'zh-CN', voicePattern: /zh[-_]CN|chinese.*china|mandarin/i },
  'ja-JP': { code: 'ja-JP', voicePattern: /ja[-_]JP|japanese/i },
  'ko-KR': { code: 'ko-KR', voicePattern: /ko[-_]KR|korean/i }
};

// Voice command patterns
const VOICE_COMMAND_PATTERNS = [
  {
    pattern: /where\s+is\s+(my\s+)?gate/i,
    action: 'show_gate',
    extract: (text: string) => ({ query: 'gate' })
  },
  {
    pattern: /show\s+security(\s+lines?)?/i,
    action: 'show_security',
    extract: (text: string) => ({ query: 'security' })
  },
  {
    pattern: /find\s+(the\s+)?(\w+)/i,
    action: 'find_location',
    extract: (text: string) => {
      const match = text.match(/find\s+(the\s+)?(\w+)/i);
      return { location: match ? match[2] : '' };
    }
  },
  {
    pattern: /navigate\s+to\s+(.+)/i,
    action: 'navigate_to',
    extract: (text: string) => {
      const match = text.match(/navigate\s+to\s+(.+)/i);
      return { destination: match ? match[1] : '' };
    }
  },
  {
    pattern: /how\s+far\s+(is|to)/i,
    action: 'query_distance',
    extract: (text: string) => ({ query: 'distance' })
  },
  {
    pattern: /stop\s+navigation/i,
    action: 'stop_navigation',
    extract: (text: string) => ({})
  },
  {
    pattern: /repeat|say\s+again/i,
    action: 'repeat_instruction',
    extract: (text: string) => ({})
  },
  {
    pattern: /(start|begin)\s+navigation/i,
    action: 'start_navigation',
    extract: (text: string) => ({})
  }
];

/**
 * Custom hook for voice navigation
 */
export const useVoiceNavigation = (options: VoiceNavigationOptions = {}) => {
  const {
    language = 'en-US',
    autoSpeak = true,
    voiceCommandsEnabled = true,
    volume = 1.0,
    rate = 1.0,
    pitch = 1.0
  } = options;

  // State
  const [state, setState] = useState<VoiceNavigationState>({
    isSupported: false,
    isSpeaking: false,
    isListening: false,
    lastSpoken: null,
    lastCommand: null,
    error: null,
    availableVoices: [],
    selectedVoice: null
  });

  // Refs
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const recognitionRef = useRef<any>(null);
  const utteranceQueueRef = useRef<SpeechSynthesisUtterance[]>([]);
  const lastInstructionRef = useRef<string | null>(null);

  // Initialize speech synthesis
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const checkSupport = () => {
      const speechSupported = 'speechSynthesis' in window;
      const recognitionSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

      setState(prev => ({
        ...prev,
        isSupported: speechSupported && recognitionSupported
      }));

      if (speechSupported) {
        synthRef.current = window.speechSynthesis;
        loadVoices();
      }
    };

    checkSupport();
  }, []);

  // Load available voices
  const loadVoices = useCallback(() => {
    if (!synthRef.current) return;

    const voices = synthRef.current.getVoices();
    if (voices.length > 0) {
      setState(prev => ({
        ...prev,
        availableVoices: voices,
        selectedVoice: findBestVoice(voices, language)
      }));
    }

    // Voices might load asynchronously
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = () => {
        const newVoices = synthRef.current!.getVoices();
        setState(prev => ({
          ...prev,
          availableVoices: newVoices,
          selectedVoice: findBestVoice(newVoices, language)
        }));
      };
    }
  }, [language]);

  // Find best matching voice for language
  const findBestVoice = (voices: SpeechSynthesisVoice[], lang: string): SpeechSynthesisVoice | null => {
    const config = LANGUAGE_CONFIGS[lang];
    if (!config) return voices[0] || null;

    // Try to find voice matching the language pattern
    const matchedVoice = voices.find(voice =>
      config.voicePattern.test(voice.name) || voice.lang === config.code
    );

    // Fallback to first voice of the language
    if (!matchedVoice) {
      const langCode = config.code.split('-')[0];
      return voices.find(voice => voice.lang.startsWith(langCode)) || voices[0] || null;
    }

    return matchedVoice;
  };

  // Speak text using speech synthesis
  const speak = useCallback((
    instruction: NavigationInstruction | string,
    interrupt: boolean = false
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!synthRef.current || !state.isSupported) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      // Parse instruction
      const text = typeof instruction === 'string' ? instruction : formatInstruction(instruction);

      // Cancel current speech if interrupt is true
      if (interrupt && synthRef.current.speaking) {
        synthRef.current.cancel();
        utteranceQueueRef.current = [];
      }

      // Create utterance
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.volume = volume;
      utterance.rate = rate;
      utterance.pitch = pitch;

      if (state.selectedVoice) {
        utterance.voice = state.selectedVoice;
      }

      // Event handlers
      utterance.onstart = () => {
        setState(prev => ({ ...prev, isSpeaking: true, lastSpoken: text }));
        lastInstructionRef.current = text;
      };

      utterance.onend = () => {
        setState(prev => ({ ...prev, isSpeaking: false }));
        processQueue();
        resolve();
      };

      utterance.onerror = (event) => {
        setState(prev => ({
          ...prev,
          isSpeaking: false,
          error: `Speech error: ${event.error}`
        }));
        reject(new Error(`Speech error: ${event.error}`));
      };

      // Add to queue or speak immediately
      if (synthRef.current.speaking && !interrupt) {
        utteranceQueueRef.current.push(utterance);
      } else {
        synthRef.current.speak(utterance);
      }
    });
  }, [state.isSupported, state.selectedVoice, language, volume, rate, pitch]);

  // Process utterance queue
  const processQueue = useCallback(() => {
    if (!synthRef.current) return;

    if (utteranceQueueRef.current.length > 0 && !synthRef.current.speaking) {
      const nextUtterance = utteranceQueueRef.current.shift();
      if (nextUtterance) {
        synthRef.current.speak(nextUtterance);
      }
    }
  }, []);

  // Format navigation instruction for speech
  const formatInstruction = (instruction: NavigationInstruction): string => {
    let text = instruction.text;

    // Add distance information
    if (instruction.distance !== undefined) {
      const distanceText = formatDistance(instruction.distance);
      text = `In ${distanceText}, ${text}`;
    }

    // Add directional emphasis
    if (instruction.direction) {
      const directionMap: Record<string, string> = {
        left: 'turn left',
        right: 'turn right',
        forward: 'continue straight',
        backward: 'turn around',
        up: 'go upstairs',
        down: 'go downstairs'
      };
      text = text.replace(
        new RegExp(instruction.direction, 'gi'),
        directionMap[instruction.direction] || instruction.direction
      );
    }

    return text;
  };

  // Format distance for speech
  const formatDistance = (meters: number): string => {
    if (meters < 10) {
      return 'a few meters';
    } else if (meters < 100) {
      const rounded = Math.round(meters / 10) * 10;
      return `${rounded} meters`;
    } else if (meters < 1000) {
      const rounded = Math.round(meters / 50) * 50;
      return `${rounded} meters`;
    } else {
      const km = (meters / 1000).toFixed(1);
      return `${km} kilometers`;
    }
  };

  // Start voice recognition
  const startListening = useCallback((
    onCommand?: (command: VoiceCommand) => void
  ): void => {
    if (!state.isSupported || !voiceCommandsEnabled) {
      setState(prev => ({ ...prev, error: 'Voice commands not supported' }));
      return;
    }

    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.lang = language;
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setState(prev => ({ ...prev, isListening: true, error: null }));
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        const command = parseVoiceCommand(transcript);

        if (command) {
          setState(prev => ({ ...prev, lastCommand: command }));
          if (onCommand) {
            onCommand(command);
          }

          // Provide audio feedback
          speak('Command recognized', true);
        }
      };

      recognition.onerror = (event: any) => {
        setState(prev => ({
          ...prev,
          isListening: false,
          error: `Recognition error: ${event.error}`
        }));
      };

      recognition.onend = () => {
        setState(prev => ({ ...prev, isListening: false }));
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: `Failed to start voice recognition: ${error}`
      }));
    }
  }, [state.isSupported, voiceCommandsEnabled, language, speak]);

  // Stop voice recognition
  const stopListening = useCallback((): void => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
      setState(prev => ({ ...prev, isListening: false }));
    }
  }, []);

  // Parse voice command
  const parseVoiceCommand = (transcript: string): VoiceCommand | null => {
    const normalizedText = transcript.toLowerCase().trim();

    for (const pattern of VOICE_COMMAND_PATTERNS) {
      if (pattern.pattern.test(normalizedText)) {
        return {
          command: transcript,
          action: pattern.action,
          parameters: pattern.extract(normalizedText)
        };
      }
    }

    return null;
  };

  // Stop speaking
  const stopSpeaking = useCallback((): void => {
    if (synthRef.current) {
      synthRef.current.cancel();
      utteranceQueueRef.current = [];
      setState(prev => ({ ...prev, isSpeaking: false }));
    }
  }, []);

  // Repeat last instruction
  const repeatLastInstruction = useCallback((): Promise<void> => {
    if (lastInstructionRef.current) {
      return speak(lastInstructionRef.current, true);
    }
    return Promise.reject(new Error('No instruction to repeat'));
  }, [speak]);

  // Change voice
  const setVoice = useCallback((voice: SpeechSynthesisVoice): void => {
    setState(prev => ({ ...prev, selectedVoice: voice }));
  }, []);

  // Announce arrival
  const announceArrival = useCallback((locationName: string): Promise<void> => {
    return speak({
      text: `You have arrived at ${locationName}`,
      priority: 'high'
    }, true);
  }, [speak]);

  // Announce distance update
  const announceDistance = useCallback((distance: number, destination: string): Promise<void> => {
    const distanceText = formatDistance(distance);
    return speak({
      text: `${distanceText} to ${destination}`,
      priority: 'normal'
    });
  }, [speak]);

  // Cleanup
  useEffect(() => {
    return () => {
      stopSpeaking();
      stopListening();
    };
  }, [stopSpeaking, stopListening]);

  return {
    // State
    ...state,

    // Methods
    speak,
    stopSpeaking,
    startListening,
    stopListening,
    repeatLastInstruction,
    setVoice,
    announceArrival,
    announceDistance,

    // Helpers
    formatDistance,
    formatInstruction
  };
};

export default useVoiceNavigation;
