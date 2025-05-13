import axios, { AxiosError } from 'axios'
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import { ActionType } from '@/models/ActionType';
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
  ): Promise<Facet[] | AnswerSet[] | string | undefined> => {
    try {
      const response = await axios.post<{ output: string }>(`${hostUrl}/send-planpilot-command`, {
        command,
      })
      const output = response.data.output;

      if(command === '?' || command === '#??' || command === '#!!') {
        return parseFacetOutput(output);
      }

      if(command.startsWith('!')) {
        return parseSolutionOutput(output);
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

  const facetStr = buildFacetString(facet);
  const command =
    newState === SelectionState.Positive
      ? `+ ${facetStr}`
      : newState === SelectionState.Negative
      ? `- ${facetStr}`
      : null; //TODO: is there a way to make a facet neutral again?

  if (command) {
    try {
      await sendPlanPilotCommand(command);
      const output = await sendPlanPilotCommand('?');
      // Handle the output to parse it into Facet[]
      if (typeof output === 'string') {
        const facets = parseFacetOutput(output);
        return facets;
      }
      // If the output is already of type Facet[]
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
  const action = facet.action;
  const const1 = `constant("${facet.constant1}")`;
  const const2 = facet.constant2 ? `,constant("${facet.constant2}")` : '';
  return `occurs(action(("${action}",${const1}${const2})),${facet.timestep})`;
}

function parseFacetOutput(output: string): Facet[] {
  try {
    const data = JSON.parse(output);

    // Check if facets are present and are in an array
    if (data.facets && Array.isArray(data.facets)) {
      return data.facets.map((facetData: Facet) => ({
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
function parseSolutionOutput(output: string): AnswerSet[] {
  try {
    const data = JSON.parse(output);

    if (data && typeof data === 'object') {
      // Map each solution to a Facet array
      return Object.entries(data).map(([solutionLabel, facets]) => {
        if (Array.isArray(facets)) {
          return {
            [solutionLabel]: facets.map((facetData: Facet) => ({
              ...facetData,
              reduction: facetData.reduction ?? { answer_set: null, facets: null },
              remaining: facetData.remaining ?? { answer_set: null, facets: null },
              selectionState: facetData.selectionState ?? SelectionState.NotSelected,
            })),
          };
        } else {
          throw new Error('Invalid facets structure within solution');
        }
      });
    } else {
      throw new Error('Invalid solution structure in the response');
    }
  } catch (error) {
    console.error('Error parsing solution output:', error);
    return [];
  }
}
