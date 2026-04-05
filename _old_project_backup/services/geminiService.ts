import { GoogleGenAI, Type, GenerateContentResponse, Modality } from "@google/genai";
import { UserProfile } from "../types";
import { callN8nWebhook } from "./n8nService";

const getAI = () => {
  const customKey = localStorage.getItem('google_api_key');
  return new GoogleGenAI({ apiKey: customKey || process.env.API_KEY || '' });
};

const getPersonalizedInstruction = (profile?: UserProfile) => {
  let base = "You are EduMind AI, a friendly, encouraging, and highly intelligent learning guide. Your goal is to help students understand complex concepts through clear explanations.";

  if (profile) {
    base += ` The user's name is ${profile.name}. They are interested in: ${profile.hobbies}. Their learning goals are: ${profile.goals}. 
    IMPORTANT: Whenever possible, use their interests and hobbies to create relatable analogies and examples. For instance, if they like sports, use sports metaphors to explain science.`;
  }

  base += " If thinking mode is on, provide deep reasoning before your final answer.";
  return base;
};

export const chatWithGemini = async (
  message: string,
  history: { role: 'user' | 'model', parts: { text: string }[] }[] = [],
  useThinking: boolean = false,
  profile?: UserProfile
): Promise<string> => {
  // Check for n8n Override
  const useN8n = localStorage.getItem('use_n8n') === 'true';
  const webhookUrl = localStorage.getItem('n8n_webhook_url');

  if (useN8n && webhookUrl) {
    return await callN8nWebhook(message, webhookUrl, history);
  }

  const ai = getAI();
  const model = 'gemini-2.0-flash-exp'; // Updated to latest flash for speed, or stick to pro

  const config: any = {
    systemInstruction: getPersonalizedInstruction(profile),
  };

  if (useThinking) {
    // Note: Thinking models might have specific configurations
    // config.thinkingConfig = { thinkingBudget: 32768 };
  }

  const chat = ai.chats.create({
    model,
    config,
    history
  });

  const result = await chat.sendMessage({ message });
  return result.text || "I'm sorry, I couldn't generate a response.";
};

export const analyzeImage = async (imageB64: string, prompt: string, profile?: UserProfile): Promise<string> => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: {
      parts: [
        { inlineData: { data: imageB64, mimeType: 'image/jpeg' } },
        { text: `${prompt}. Personalized for ${profile?.name || 'the user'} who likes ${profile?.hobbies || 'learning'}.` }
      ]
    },
    config: {
      systemInstruction: getPersonalizedInstruction(profile)
    }
  });
  return response.text || "No analysis available.";
};

export const generateCourseOutline = async (description: string, profile?: UserProfile): Promise<any[]> => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: `Generate a 4-step learning path outline for: ${description}. Consider that the user is interested in ${profile?.hobbies || 'various topics'}. Return as JSON array of objects with title, description, category, and estimated time.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            title: { type: Type.STRING },
            description: { type: Type.STRING },
            category: { type: Type.STRING },
            time: { type: Type.STRING }
          },
          required: ["title", "description", "category", "time"]
        }
      }
    }
  });

  try {
    return JSON.parse(response.text || "[]");
  } catch (e) {
    return [];
  }
};

export const generateSpeech = async (text: string): Promise<ArrayBuffer> => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: {
        voiceConfig: {
          prebuiltVoiceConfig: { voiceName: 'Kore' },
        },
      },
    },
  });



  const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) throw new Error("No audio data returned");

  const binaryString = atob(base64Audio);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};

export const generateN8nWorkflow = async (description: string): Promise<string> => {
  const ai = getAI();
  const model = 'gemini-1.5-flash';

  const systemPrompt = `
    You are an expert in n8n automation. Your task is to generate a valid n8n workflow JSON based on the user's description.
    
    RULES:
    1. OUTPUT ONLY JSON. No markdown, no explanations.
    2. The JSON must follow the standard n8n workflow structure: { "nodes": [], "connections": {} }.
    3. Always include a 'Webhook' node (trigger) at the start.
    4. Default search for nodes: 'n8n-nodes-base.[nodeType]'.
    5. Ensure valid connections between nodes.
    6. If the user asks for AI, use 'n8n-nodes-base.googleGemini' or generic 'function' node as placeholder.
    
    Example Structure:
    {
      "name": "Generated Workflow",
      "nodes": [...],
      "connections": {...}
    }
  `;

  const chat = ai.chats.create({
    model,
    config: {
      systemInstruction: systemPrompt,
      responseMimeType: "application/json"
    }
  });

  try {
    const result = await chat.sendMessage({ message: description });
    return result.text || "{}";
  } catch (error) {
    console.error("Error generating workflow:", error);
    throw error;
  }
};
