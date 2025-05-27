import axios, { AxiosError } from 'axios'
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import type { AnswerSet } from '@/models/AnswerSet';

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
    encoding: string,
    abstractTimeStep: boolean,
  ): Promise<Facet[] | undefined> => {
    try {
      const response = await axios.post<{ output: Facet[] }>(
        `${hostUrl}/run-planpilot`,
        {
          sasFile,
          horizon,
          encoding,
          abstractTimeStep,
        }
      );
      return parseFacetOutput(response.data.output as Facet[]);
    } catch (error) {
      handleError(error);
    }
  };

export const sendPlanPilotCommand = async (
    command: string
  ): Promise<Facet[] | AnswerSet[] | string | undefined> => {
    try {
      const response = await axios.post<{ output: Facet[] | AnswerSet[] | string }>(`${hostUrl}/send-planpilot-command`, {
        command,
      })
      const output = response.data.output;

      console.log("send plan pilot command: ", command);
      console.log("send plan pilot command output:", output);

      if (command === '?' || command === '#??' || command === '#!!' || command.startsWith('|= %')) {
        if (Array.isArray(output) && output.length > 0 && 'reduction' in output[0]) {
          return parseFacetOutput(output as Facet[]);
        } else if (output.length === 0) {
          return [];
        } else {
          console.error('Unexpected facet output format:', output);
          return [];
        }
      }

      if (command.startsWith('!')) {
        if (Array.isArray(output)) {
          return parseSolutionOutput(output as AnswerSet[]);
        } else {
          console.error('Unexpected solution output format:', output);
          return [];
        }
      }

      return output;
    } catch (error) {
      handleError(error)
    }
  }

export const updateSelectionState = async (
  facet: Facet,
  newState: SelectionState
): Promise<Facet[] | undefined> => {
  facet.selectionState = newState;

  //const facetStr = buildFacetString(facet);
  const facetStr = facet.id;
  let command;
  if (newState === SelectionState.Positive) {
    command = `+ ${facetStr}`;
  } else if (newState === SelectionState.Negative) {
    command = `+ ~${facetStr}`;
  } else if (newState === SelectionState.NotSelected && facet.selectionState === SelectionState.Negative) {
    command = `- ~${facetStr}`;
  } else {
    command = `- ${facetStr}`;
  }
  if (command) {
    try {
      const output = await sendPlanPilotCommand(command);
      if (Array.isArray(output)) {
        return output as Facet[];
      }
      return undefined;
    } catch (error) {
      console.error('Failed to update facet on backend:', error);
    }
  }

  return undefined;
};

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

function buildFacetString(facet: Facet): string {
  const const2 = facet.constant2 ? `,"${facet.constant2}"` : '';
  return `occurs(action(("${facet.action}","${facet.constant1}"${const2})),${facet.timestep})`;
}

function parseFacetOutput(output: Facet[]): Facet[] {
  try {
    if (Array.isArray(output)) {
      return output.map((facetData: Facet) => ({
        ...facetData,
        reduction: facetData.reduction ?? { answer_set: null, facets: null },
        remaining: facetData.remaining ?? { answer_set: null, facets: null },
      }));
    } else {
      throw new Error('Invalid facet structure in the response');
    }
  } catch (error) {
    console.error('Error parsing facet output:', error);
    return [];
  }
}

// Function to parse the solution output
function parseSolutionOutput(output: AnswerSet[]): AnswerSet[] {
  try {
    if (Array.isArray(output)) {
      return output.map((answerSetData: any) => {
        if (answerSetData && answerSetData.label && Array.isArray(answerSetData.facets)) {
          const { label, facets } = answerSetData;

          const processedFacets = facets.map((facetData: Facet) => ({
            ...facetData,
            reduction: facetData.reduction ?? { answer_set: { positive: null, negative: null }, facets: { positive: null, negative: null } },
            remaining: facetData.remaining ?? { answer_set: { positive: null, negative: null }, facets: { positive: null, negative: null } },
            selectionState: facetData.selectionState ?? SelectionState.NotSelected,
          }));

          return { label, facets: processedFacets };
        } else {
          throw new Error('Invalid answer set structure in the response');
        }
      });
    } else {
      throw new Error('Expected array structure for solution output');
    }
  } catch (error) {
    console.error('Error parsing solution output:', error);
    return [];
  }
}
