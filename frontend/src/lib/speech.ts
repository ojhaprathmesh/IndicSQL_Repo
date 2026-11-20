import { apiClient } from "@/lib/api-client";

export function isAudioRecordingSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof MediaRecorder !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia)
  );
}

export class AudioRecorder {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: BlobPart[] = [];

  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.recorder = new MediaRecorder(this.stream);
    this.recorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) this.chunks.push(event.data);
    });
    this.recorder.start();
  }

  stop(): Promise<Blob> {
    const recorder = this.recorder;
    if (!recorder || recorder.state !== "recording") {
      return Promise.reject(new Error("No audio recording is in progress."));
    }

    return new Promise((resolve, reject) => {
      recorder.addEventListener(
        "stop",
        () => {
          const audio = new Blob(this.chunks, {
            type: recorder.mimeType || "audio/webm",
          });
          this.cleanup();
          resolve(audio);
        },
        { once: true }
      );
      recorder.addEventListener(
        "error",
        () => {
          this.cleanup();
          reject(new Error("Audio recording failed."));
        },
        { once: true }
      );
      recorder.stop();
    });
  }

  cleanup(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
  }
}

const LANGUAGE_CODES: Record<string, string> = {
  bn: "bn-IN",
  en: "en-IN",
  "hi-en": "hi-IN",
  hi: "hi-IN",
  mr: "mr-IN",
  ta: "ta-IN",
  te: "te-IN",
};

export async function playTextToSpeech(
  text: string,
  language: string,
  onEnded: () => void,
  onError: (message?: string) => void
): Promise<() => void> {
  try {
    const response = await apiClient.synthesizeSpeech({
      text,
      language_code: LANGUAGE_CODES[language.toLowerCase()] || "hi-IN",
    });
    if (!response.audio_base64) {
      throw new Error("The speech service returned no audio.");
    }

    const binary = atob(response.audio_base64);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const audioUrl = URL.createObjectURL(
      new Blob([bytes], { type: "audio/wav" })
    );
    const audio = new Audio(audioUrl);
    audio.addEventListener(
      "ended",
      () => {
        URL.revokeObjectURL(audioUrl);
        onEnded();
      },
      { once: true }
    );
    audio.addEventListener(
      "error",
      () => {
        URL.revokeObjectURL(audioUrl);
        onError("Audio playback failed.");
      },
      { once: true }
    );
    await audio.play();
    return () => {
      audio.pause();
      audio.currentTime = 0;
      URL.revokeObjectURL(audioUrl);
      onEnded();
    };
  } catch (error) {
    onError(
      error instanceof Error ? error.message : "Speech synthesis failed."
    );
    return () => {};
  }
}
