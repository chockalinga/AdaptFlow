import axios from 'axios';
import { FrameworkConfig } from '../types/frameworks';

const API_BASE_URL = 'http://localhost:8000/api';

export interface Framework {
  id: string;
  name: string;
  description: string;
}

export interface GenerateCodeRequest {
  prompt: string;
  framework: string;
}

export interface GenerateCodeResponse {
  config: FrameworkConfig;  // Using the union type from frameworks.ts
  code: string;
}

export const api = {
  getFrameworks: async (): Promise<Framework[]> => {
    const response = await axios.get(`${API_BASE_URL}/frameworks`);
    return response.data;
  },

  generateCode: async (request: GenerateCodeRequest): Promise<GenerateCodeResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-code`, request);
    return response.data;
  },
};
