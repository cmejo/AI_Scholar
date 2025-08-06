/**
 * Multilingual Voice Service for language detection and cross-language voice interaction
 */

import voiceService, { VoiceConfig, TranscriptionResult } from './voiceService';

export interface LanguageConfig {
  code: string;
  name: string;
  nativeName: string;
  region?: string;
  rtl: boolean;
  voiceSupport: boolean;
  recognitionSupport: boolean;
  confidence: number;
}

export interface LanguageDetectionResult {
  detectedLanguage: string;
  confidence: number;
  alternatives: Array<{
    language: string;
    confidence: number;
  }>;
}

export interface MultilingualTranscription extends TranscriptionResult {
  detectedLanguage: string;
  originalLanguage: string;
  translation?: {
    text: string;
    targetLanguage: string;
    confidence: number;
  };
}

export interface VoiceCommandPattern {
  language: string;
  patterns: Record<string, string[]>;
  entities: Record<string, string[]>;
}

class MultilingualVoiceService {
  private supportedLanguages: Map<string, LanguageConfig> = new Map();
  private languagePatterns: Map<string, VoiceCommandPattern> = new Map();
  private currentLanguage: string = 'en-US';
  private autoDetectLanguage: boolean = true;
  private translationEnabled: boolean = false;
  private languageHistory: string[] = [];

  constructor() {
    this.initializeSupportedLanguages();
    this.initializeLanguagePatterns();
  }

  /**
   * Initialize supported languages with their configurations
   */
  private initializeSupportedLanguages(): void {
    const languages: LanguageConfig[] = [
      {
        code: 'en-US',
        name: 'English (US)',
        nativeName: 'English',
        region: 'United States',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.95
      },
      {
        code: 'en-GB',
        name: 'English (UK)',
        nativeName: 'English',
        region: 'United Kingdom',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.95
      },
      {
        code: 'es-ES',
        name: 'Spanish (Spain)',
        nativeName: 'Español',
        region: 'Spain',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.9
      },
      {
        code: 'es-MX',
        name: 'Spanish (Mexico)',
        nativeName: 'Español',
        region: 'Mexico',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.9
      },
      {
        code: 'fr-FR',
        name: 'French (France)',
        nativeName: 'Français',
        region: 'France',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.9
      },
      {
        code: 'de-DE',
        name: 'German (Germany)',
        nativeName: 'Deutsch',
        region: 'Germany',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.9
      },
      {
        code: 'it-IT',
        name: 'Italian (Italy)',
        nativeName: 'Italiano',
        region: 'Italy',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.85
      },
      {
        code: 'pt-BR',
        name: 'Portuguese (Brazil)',
        nativeName: 'Português',
        region: 'Brazil',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.85
      },
      {
        code: 'ru-RU',
        name: 'Russian (Russia)',
        nativeName: 'Русский',
        region: 'Russia',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'ja-JP',
        name: 'Japanese (Japan)',
        nativeName: '日本語',
        region: 'Japan',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'ko-KR',
        name: 'Korean (South Korea)',
        nativeName: '한국어',
        region: 'South Korea',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'zh-CN',
        name: 'Chinese (Simplified)',
        nativeName: '中文',
        region: 'China',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'zh-TW',
        name: 'Chinese (Traditional)',
        nativeName: '中文',
        region: 'Taiwan',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'ar-SA',
        name: 'Arabic (Saudi Arabia)',
        nativeName: 'العربية',
        region: 'Saudi Arabia',
        rtl: true,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.75
      },
      {
        code: 'hi-IN',
        name: 'Hindi (India)',
        nativeName: 'हिन्दी',
        region: 'India',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.75
      },
      {
        code: 'nl-NL',
        name: 'Dutch (Netherlands)',
        nativeName: 'Nederlands',
        region: 'Netherlands',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'sv-SE',
        name: 'Swedish (Sweden)',
        nativeName: 'Svenska',
        region: 'Sweden',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'no-NO',
        name: 'Norwegian (Norway)',
        nativeName: 'Norsk',
        region: 'Norway',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'da-DK',
        name: 'Danish (Denmark)',
        nativeName: 'Dansk',
        region: 'Denmark',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.8
      },
      {
        code: 'fi-FI',
        name: 'Finnish (Finland)',
        nativeName: 'Suomi',
        region: 'Finland',
        rtl: false,
        voiceSupport: true,
        recognitionSupport: true,
        confidence: 0.75
      }
    ];

    languages.forEach(lang => {
      this.supportedLanguages.set(lang.code, lang);
    });
  }

  /**
   * Initialize language-specific command patterns
   */
  private initializeLanguagePatterns(): void {
    // English patterns
    this.languagePatterns.set('en-US', {
      language: 'en-US',
      patterns: {
        search: ['search for', 'find', 'look for', 'show me'],
        navigate: ['go to', 'open', 'navigate to', 'take me to'],
        document: ['upload document', 'open file', 'delete document', 'summarize'],
        help: ['help', 'what can you do', 'assistance'],
        stop: ['stop', 'cancel', 'quit', 'pause']
      },
      entities: {
        document_types: ['document', 'file', 'paper', 'pdf', 'text'],
        pages: ['home', 'documents', 'chat', 'settings', 'analytics'],
        actions: ['open', 'close', 'delete', 'save', 'upload', 'download']
      }
    });

    // Spanish patterns
    this.languagePatterns.set('es-ES', {
      language: 'es-ES',
      patterns: {
        search: ['buscar', 'encontrar', 'busca', 'muéstrame'],
        navigate: ['ir a', 'abrir', 'navegar a', 'llévame a'],
        document: ['subir documento', 'abrir archivo', 'eliminar documento', 'resumir'],
        help: ['ayuda', 'qué puedes hacer', 'asistencia'],
        stop: ['parar', 'cancelar', 'salir', 'pausar']
      },
      entities: {
        document_types: ['documento', 'archivo', 'papel', 'pdf', 'texto'],
        pages: ['inicio', 'documentos', 'chat', 'configuración', 'análisis'],
        actions: ['abrir', 'cerrar', 'eliminar', 'guardar', 'subir', 'descargar']
      }
    });

    // French patterns
    this.languagePatterns.set('fr-FR', {
      language: 'fr-FR',
      patterns: {
        search: ['chercher', 'trouver', 'rechercher', 'montrez-moi'],
        navigate: ['aller à', 'ouvrir', 'naviguer vers', 'emmenez-moi à'],
        document: ['télécharger document', 'ouvrir fichier', 'supprimer document', 'résumer'],
        help: ['aide', 'que pouvez-vous faire', 'assistance'],
        stop: ['arrêter', 'annuler', 'quitter', 'pause']
      },
      entities: {
        document_types: ['document', 'fichier', 'papier', 'pdf', 'texte'],
        pages: ['accueil', 'documents', 'chat', 'paramètres', 'analyses'],
        actions: ['ouvrir', 'fermer', 'supprimer', 'sauvegarder', 'télécharger']
      }
    });

    // German patterns
    this.languagePatterns.set('de-DE', {
      language: 'de-DE',
      patterns: {
        search: ['suchen', 'finden', 'suche nach', 'zeig mir'],
        navigate: ['gehe zu', 'öffnen', 'navigiere zu', 'bring mich zu'],
        document: ['dokument hochladen', 'datei öffnen', 'dokument löschen', 'zusammenfassen'],
        help: ['hilfe', 'was kannst du tun', 'unterstützung'],
        stop: ['stoppen', 'abbrechen', 'beenden', 'pausieren']
      },
      entities: {
        document_types: ['dokument', 'datei', 'papier', 'pdf', 'text'],
        pages: ['startseite', 'dokumente', 'chat', 'einstellungen', 'analysen'],
        actions: ['öffnen', 'schließen', 'löschen', 'speichern', 'hochladen', 'herunterladen']
      }
    });

    // Japanese patterns
    this.languagePatterns.set('ja-JP', {
      language: 'ja-JP',
      patterns: {
        search: ['検索', '探す', '見つける', '見せて'],
        navigate: ['行く', '開く', 'ナビゲート', '連れて行く'],
        document: ['ドキュメントアップロード', 'ファイルを開く', 'ドキュメント削除', '要約'],
        help: ['ヘルプ', '何ができますか', 'サポート'],
        stop: ['停止', 'キャンセル', '終了', '一時停止']
      },
      entities: {
        document_types: ['ドキュメント', 'ファイル', '論文', 'PDF', 'テキスト'],
        pages: ['ホーム', 'ドキュメント', 'チャット', '設定', '分析'],
        actions: ['開く', '閉じる', '削除', '保存', 'アップロード', 'ダウンロード']
      }
    });

    // Chinese patterns
    this.languagePatterns.set('zh-CN', {
      language: 'zh-CN',
      patterns: {
        search: ['搜索', '查找', '寻找', '显示'],
        navigate: ['转到', '打开', '导航到', '带我去'],
        document: ['上传文档', '打开文件', '删除文档', '总结'],
        help: ['帮助', '你能做什么', '协助'],
        stop: ['停止', '取消', '退出', '暂停']
      },
      entities: {
        document_types: ['文档', '文件', '论文', 'PDF', '文本'],
        pages: ['主页', '文档', '聊天', '设置', '分析'],
        actions: ['打开', '关闭', '删除', '保存', '上传', '下载']
      }
    });

    // Arabic patterns
    this.languagePatterns.set('ar-SA', {
      language: 'ar-SA',
      patterns: {
        search: ['بحث', 'ابحث عن', 'اعثر على', 'أظهر لي'],
        navigate: ['اذهب إلى', 'افتح', 'انتقل إلى', 'خذني إلى'],
        document: ['رفع مستند', 'فتح ملف', 'حذف مستند', 'تلخيص'],
        help: ['مساعدة', 'ماذا يمكنك أن تفعل', 'مساعدة'],
        stop: ['توقف', 'إلغاء', 'خروج', 'إيقاف مؤقت']
      },
      entities: {
        document_types: ['مستند', 'ملف', 'ورقة', 'PDF', 'نص'],
        pages: ['الرئيسية', 'المستندات', 'الدردشة', 'الإعدادات', 'التحليلات'],
        actions: ['فتح', 'إغلاق', 'حذف', 'حفظ', 'رفع', 'تحميل']
      }
    });
  }

  /**
   * Detect language from audio or text
   */
  async detectLanguage(input: string | Blob): Promise<LanguageDetectionResult> {
    try {
      if (typeof input === 'string') {
        return this.detectLanguageFromText(input);
      } else {
        return await this.detectLanguageFromAudio(input);
      }
    } catch (error) {
      console.error('Language detection failed:', error);
      return {
        detectedLanguage: this.currentLanguage,
        confidence: 0.5,
        alternatives: []
      };
    }
  }

  /**
   * Detect language from text using pattern matching and character analysis
   */
  private detectLanguageFromText(text: string): LanguageDetectionResult {
    const scores: Record<string, number> = {};
    const normalizedText = text.toLowerCase().trim();

    // Pattern-based detection
    for (const [langCode, patterns] of this.languagePatterns.entries()) {
      let score = 0;
      
      // Check command patterns
      for (const patternGroup of Object.values(patterns.patterns)) {
        for (const pattern of patternGroup) {
          if (normalizedText.includes(pattern.toLowerCase())) {
            score += 2;
          }
        }
      }
      
      // Check entity patterns
      for (const entityGroup of Object.values(patterns.entities)) {
        for (const entity of entityGroup) {
          if (normalizedText.includes(entity.toLowerCase())) {
            score += 1;
          }
        }
      }
      
      scores[langCode] = score;
    }

    // Character-based detection for non-Latin scripts
    const characterScores = this.analyzeCharacterSets(text);
    
    // Combine scores
    for (const [langCode, charScore] of Object.entries(characterScores)) {
      scores[langCode] = (scores[langCode] || 0) + charScore * 3;
    }

    // Find best match
    const sortedScores = Object.entries(scores)
      .filter(([_, score]) => score > 0)
      .sort(([, a], [, b]) => b - a);

    if (sortedScores.length === 0) {
      return {
        detectedLanguage: this.currentLanguage,
        confidence: 0.3,
        alternatives: []
      };
    }

    const [bestLang, bestScore] = sortedScores[0];
    const maxPossibleScore = 10; // Adjust based on scoring system
    const confidence = Math.min(0.95, bestScore / maxPossibleScore);

    const alternatives = sortedScores.slice(1, 4).map(([lang, score]) => ({
      language: lang,
      confidence: Math.min(0.9, score / maxPossibleScore)
    }));

    return {
      detectedLanguage: bestLang,
      confidence,
      alternatives
    };
  }

  /**
   * Analyze character sets to detect language
   */
  private analyzeCharacterSets(text: string): Record<string, number> {
    const scores: Record<string, number> = {};
    
    // Character set patterns
    const patterns = {
      'zh-CN': /[\u4e00-\u9fff]/g, // Chinese characters
      'ja-JP': /[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]/g, // Hiragana, Katakana, Kanji
      'ko-KR': /[\uac00-\ud7af]/g, // Hangul
      'ar-SA': /[\u0600-\u06ff]/g, // Arabic
      'ru-RU': /[\u0400-\u04ff]/g, // Cyrillic
      'hi-IN': /[\u0900-\u097f]/g, // Devanagari
    };

    for (const [langCode, pattern] of Object.entries(patterns)) {
      const matches = text.match(pattern);
      if (matches) {
        scores[langCode] = matches.length / text.length;
      }
    }

    return scores;
  }

  /**
   * Detect language from audio using server-side processing
   */
  private async detectLanguageFromAudio(audioBlob: Blob): Promise<LanguageDetectionResult> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);

      const response = await fetch('/api/voice/detect-language', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Language detection API failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Audio language detection failed:', error);
      
      // Fallback to current language
      return {
        detectedLanguage: this.currentLanguage,
        confidence: 0.5,
        alternatives: []
      };
    }
  }

  /**
   * Perform multilingual speech recognition
   */
  async multilingualSpeechToText(audioBlob: Blob, targetLanguage?: string): Promise<MultilingualTranscription> {
    try {
      // Detect language if not specified
      let detectedLang = targetLanguage || this.currentLanguage;
      
      if (this.autoDetectLanguage && !targetLanguage) {
        const detection = await this.detectLanguageFromAudio(audioBlob);
        if (detection.confidence > 0.7) {
          detectedLang = detection.detectedLanguage;
        }
      }

      // Perform speech recognition in detected language
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('language', detectedLang);

      const response = await fetch('/api/voice/multilingual-speech-to-text', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Multilingual speech recognition failed');
      }

      const result = await response.json();

      // Add to language history
      this.addToLanguageHistory(detectedLang);

      // Translate if needed and enabled
      let translation;
      if (this.translationEnabled && detectedLang !== this.currentLanguage) {
        translation = await this.translateText(result.text, detectedLang, this.currentLanguage);
      }

      return {
        ...result,
        detectedLanguage: detectedLang,
        originalLanguage: detectedLang,
        translation
      };

    } catch (error) {
      console.error('Multilingual speech recognition failed:', error);
      throw error;
    }
  }

  /**
   * Perform multilingual text-to-speech
   */
  async multilingualTextToSpeech(text: string, language: string, voiceConfig?: VoiceConfig): Promise<Blob> {
    try {
      const langConfig = this.supportedLanguages.get(language);
      if (!langConfig || !langConfig.voiceSupport) {
        throw new Error(`Language ${language} not supported for text-to-speech`);
      }

      const requestBody = {
        text,
        language,
        config: {
          ...voiceConfig,
          language
        }
      };

      const response = await fetch('/api/voice/multilingual-text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error('Multilingual text-to-speech failed');
      }

      return await response.blob();

    } catch (error) {
      console.error('Multilingual TTS failed:', error);
      throw error;
    }
  }

  /**
   * Translate text between languages
   */
  async translateText(text: string, fromLanguage: string, toLanguage: string): Promise<{
    text: string;
    targetLanguage: string;
    confidence: number;
  }> {
    try {
      const response = await fetch('/api/voice/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text,
          from: fromLanguage,
          to: toLanguage
        })
      });

      if (!response.ok) {
        throw new Error('Translation failed');
      }

      return await response.json();

    } catch (error) {
      console.error('Translation failed:', error);
      return {
        text: text, // Return original text if translation fails
        targetLanguage: toLanguage,
        confidence: 0.0
      };
    }
  }

  /**
   * Get language-specific voice command patterns
   */
  getLanguagePatterns(language: string): VoiceCommandPattern | null {
    return this.languagePatterns.get(language) || null;
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages(): LanguageConfig[] {
    return Array.from(this.supportedLanguages.values());
  }

  /**
   * Get languages with voice support
   */
  getVoiceSupportedLanguages(): LanguageConfig[] {
    return Array.from(this.supportedLanguages.values()).filter(lang => lang.voiceSupport);
  }

  /**
   * Get languages with recognition support
   */
  getRecognitionSupportedLanguages(): LanguageConfig[] {
    return Array.from(this.supportedLanguages.values()).filter(lang => lang.recognitionSupport);
  }

  /**
   * Set current language
   */
  setCurrentLanguage(language: string): void {
    if (this.supportedLanguages.has(language)) {
      this.currentLanguage = language;
      this.addToLanguageHistory(language);
    } else {
      throw new Error(`Language ${language} is not supported`);
    }
  }

  /**
   * Get current language
   */
  getCurrentLanguage(): string {
    return this.currentLanguage;
  }

  /**
   * Enable/disable automatic language detection
   */
  setAutoDetectLanguage(enabled: boolean): void {
    this.autoDetectLanguage = enabled;
  }

  /**
   * Check if auto-detection is enabled
   */
  isAutoDetectEnabled(): boolean {
    return this.autoDetectLanguage;
  }

  /**
   * Enable/disable translation
   */
  setTranslationEnabled(enabled: boolean): void {
    this.translationEnabled = enabled;
  }

  /**
   * Check if translation is enabled
   */
  isTranslationEnabled(): boolean {
    return this.translationEnabled;
  }

  /**
   * Get language history
   */
  getLanguageHistory(): string[] {
    return [...this.languageHistory];
  }

  /**
   * Add language to history
   */
  private addToLanguageHistory(language: string): void {
    // Remove if already exists
    const index = this.languageHistory.indexOf(language);
    if (index > -1) {
      this.languageHistory.splice(index, 1);
    }

    // Add to beginning
    this.languageHistory.unshift(language);

    // Keep only last 10 languages
    if (this.languageHistory.length > 10) {
      this.languageHistory = this.languageHistory.slice(0, 10);
    }
  }

  /**
   * Get language configuration
   */
  getLanguageConfig(language: string): LanguageConfig | null {
    return this.supportedLanguages.get(language) || null;
  }

  /**
   * Check if language is RTL (right-to-left)
   */
  isRTLLanguage(language: string): boolean {
    const config = this.supportedLanguages.get(language);
    return config?.rtl || false;
  }

  /**
   * Get available voices for language
   */
  async getAvailableVoicesForLanguage(language: string): Promise<SpeechSynthesisVoice[]> {
    if (!voiceService.isTextToSpeechSupported()) {
      return [];
    }

    const allVoices = voiceService.getAvailableVoices();
    return allVoices.filter(voice => 
      voice.lang.startsWith(language.split('-')[0]) || 
      voice.lang === language
    );
  }

  /**
   * Get best voice for language
   */
  async getBestVoiceForLanguage(language: string): Promise<SpeechSynthesisVoice | null> {
    const voices = await this.getAvailableVoicesForLanguage(language);
    
    if (voices.length === 0) {
      return null;
    }

    // Prefer exact language match
    const exactMatch = voices.find(voice => voice.lang === language);
    if (exactMatch) {
      return exactMatch;
    }

    // Fallback to language family match
    const languageFamily = language.split('-')[0];
    const familyMatch = voices.find(voice => voice.lang.startsWith(languageFamily));
    
    return familyMatch || voices[0];
  }

  /**
   * Validate command in specific language
   */
  validateCommandInLanguage(command: string, language: string): {
    isValid: boolean;
    confidence: number;
    suggestedIntent?: string;
  } {
    const patterns = this.languagePatterns.get(language);
    
    if (!patterns) {
      return {
        isValid: false,
        confidence: 0,
      };
    }

    const normalizedCommand = command.toLowerCase().trim();
    let bestMatch = '';
    let bestScore = 0;

    // Check against all patterns
    for (const [intent, patternList] of Object.entries(patterns.patterns)) {
      for (const pattern of patternList) {
        if (normalizedCommand.includes(pattern.toLowerCase())) {
          const score = pattern.length / normalizedCommand.length;
          if (score > bestScore) {
            bestScore = score;
            bestMatch = intent;
          }
        }
      }
    }

    return {
      isValid: bestScore > 0.3,
      confidence: Math.min(0.95, bestScore),
      suggestedIntent: bestMatch || undefined
    };
  }

  /**
   * Get command suggestions for language
   */
  getCommandSuggestionsForLanguage(language: string, category?: string): string[] {
    const patterns = this.languagePatterns.get(language);
    
    if (!patterns) {
      return [];
    }

    const suggestions: string[] = [];
    
    for (const [intent, patternList] of Object.entries(patterns.patterns)) {
      if (!category || intent === category) {
        // Take first pattern from each intent as example
        if (patternList.length > 0) {
          suggestions.push(patternList[0]);
        }
      }
    }

    return suggestions;
  }

  /**
   * Switch to language and update interface
   */
  async switchToLanguage(language: string): Promise<void> {
    const config = this.supportedLanguages.get(language);
    
    if (!config) {
      throw new Error(`Language ${language} is not supported`);
    }

    // Update current language
    this.setCurrentLanguage(language);

    // Update document direction for RTL languages
    if (typeof document !== 'undefined') {
      document.documentElement.dir = config.rtl ? 'rtl' : 'ltr';
      document.documentElement.lang = language.split('-')[0];
    }

    // Dispatch language change event
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('languageChanged', {
        detail: { 
          language, 
          config,
          isRTL: config.rtl
        }
      });
      window.dispatchEvent(event);
    }

    console.log(`Switched to language: ${config.name} (${language})`);
  }
}

export default new MultilingualVoiceService();