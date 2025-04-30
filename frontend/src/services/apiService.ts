import axios, { AxiosError } from 'axios'
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';

let hostUrl = 'http://localhost:5000/api'

export const getSasPlan = async (
    problemFile: File,
    domainFile: File
  ): Promise<FastDownwardResponse | undefined> => {
    const formData = new FormData();
    
    formData.append('domainFile', domainFile);
    formData.append('problemFile', problemFile);
  
    try {
      const response = await axios.post<FastDownwardResponse>(hostUrl + '/run', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
        handleError(error);
    }
  };

  function handleError(error: unknown): never {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ERR_NETWORK' || error.response === undefined) {
        throw new Error('Backend not reachable.');
      }
  
      // Check for known error structure in response data
      const serverError = error.response.data as { error?: string };
      if (serverError && serverError.error) {
        throw new Error(serverError.error);
      }
  
      // If no recognizable error format, throw generic message
      throw new Error('An unexpected error occurred.');
    } else {
      // Non-Axios error (fallback)
      throw new Error('An unknown error occurred.');
    }
  }