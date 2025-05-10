import axios, { AxiosError } from 'axios'
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import type { Facet } from '@/models/Facet';

let hostUrl = 'http://localhost:5000/api'

export const getSasPlan = async (
    problemFile: File,
    domainFile: File
  ): Promise<FastDownwardResponse | undefined> => {
    const formData = new FormData();
    
    formData.append('domainFile', domainFile);
    formData.append('problemFile', problemFile);
  
    try {
      const response = await axios.post<FastDownwardResponse>(hostUrl + '/run-fastdownward', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
        handleError(error);
    }
  };

export const runPlanPilot = async (
    sasFile: string,
    horizon: number,
    encoding: string
  ): Promise<Facet[] | undefined> => {
    try {
      const response = await axios.post<{ facets: Facet[] }>(
        `${hostUrl}/run-planpilot`,
        {
          sasFile,
          horizon,
          encoding,
        }
      );
      return response.data.facets;
    } catch (error) {
      handleError(error);
    }
  };

export const sendPlanPilotCommand = async (
    command: string
  ): Promise<string | undefined> => {
    try {
      const response = await axios.post<{ output: string }>(`${hostUrl}/send-planpilot-command`, {
        command,
      })
      return response.data.output
    } catch (error) {
      handleError(error)
    }
  }

export const stopPlanPilot = async (): Promise<string | undefined> => {
    try {
      const response = await axios.post<{ status: string }>(`${hostUrl}/stop-planpilot`)
      return response.data.status
    } catch (error) {
      handleError(error)
    }
  }

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
