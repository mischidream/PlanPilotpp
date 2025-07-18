import axios, { AxiosError } from 'axios';
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import type { Solution } from '@/models/Solution';
import type { SasPlanInput } from '@/models/SasPlanInput';
import type { PlanPilotInput } from '@/models/PlanPilotInput';
import type { SelectionUpdateInput } from '@/models/SelectionUpdateInput';
import type { ActivatePlanResponse } from '@/models/ActivePlanResponse';

let hostUrl = 'http://localhost:5000/api';

export const getSasPlan = async (
  input: SasPlanInput
): Promise<FastDownwardResponse | undefined> => {
  const formData = new FormData();

  formData.append('domainFile', input.domainFile);
  formData.append('problemFile', input.problemFile);

  try {
    const response = await axios.post<FastDownwardResponse>(
      hostUrl + '/run-fastdownward',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

export const runPlanPilot = async (input: PlanPilotInput): Promise<Facet[] | undefined> => {
  try {
    const response = await axios.post<{ output: Facet[] }>(`${hostUrl}/run-planpilot`, input);
    return parseFacetOutput(response.data.output as Facet[]);
  } catch (error) {
    handleError(error);
  }
};

export const activateBestPlan = async (
  planFile: string
): Promise<ActivatePlanResponse | undefined> => {
  try {
    const response = await axios.post<ActivatePlanResponse>(`${hostUrl}/activate-plan`, {
      planFile,
    });
    console.log('best plan data timeline: ', response.data.timeline);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

export const updatePlan = async (
  changedTimestep: number,
  commands: string | string[]
): Promise<ActivatePlanResponse | undefined> => {
  try {
    const response = await axios.post<ActivatePlanResponse>(`${hostUrl}/update-plan`, {
      changedTimestep,
      commands,
    });
    console.log('timeline from plan update:', response.data.timeline);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

export const sendPlanPilotCommand = async (
  command: string
): Promise<Facet[] | Solution[] | string | undefined> => {
  try {
    const response = await axios.post<{ output: Facet[] | Solution[] | string }>(
      `${hostUrl}/send-planpilot-command`,
      {
        command,
      }
    );
    const output = response.data.output;

    console.log('send plan pilot command: ', command);
    console.log('send plan pilot command output:', output);

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
        return parseSolutionOutput(output as Solution[]);
      } else {
        console.error('Unexpected solution output format:', output);
        return [];
      }
    }

    return output;
  } catch (error) {
    handleError(error);
  }
};

export const updateSelectionState = async (
  input: SelectionUpdateInput
): Promise<Facet[] | undefined> => {
  const { facet, newState } = input;
  facet.selectionState = newState;

  //const facetStr = buildFacetString(facet);
  const facetStr = facet.id;
  let command;
  if (newState === SelectionState.Positive) {
    command = `+ ${facetStr}`;
  } else if (newState === SelectionState.Negative) {
    command = `+ ~${facetStr}`;
  } else if (
    newState === SelectionState.NotSelected &&
    facet.selectionState === SelectionState.Negative
  ) {
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
    const response = await axios.post<{ status: string }>(`${hostUrl}/stop-planpilot`);
    return response.data.status;
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

function buildFacetString(facet: Facet): string {
  const const2 = facet.constant2 ? `,"${facet.constant2}"` : '';
  return `occurs(action(("${facet.action}","${facet.constant1}"${const2})),${facet.timestep})`;
}

function parseFacetOutput(output: Facet[]): Facet[] {
  try {
    if (Array.isArray(output)) {
      return output.map((facetData: Facet) => ({
        ...facetData,
        reduction: facetData.reduction ?? { solution: null, facets: null },
        remaining: facetData.remaining ?? { solution: null, facets: null },
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
function parseSolutionOutput(output: Solution[]): Solution[] {
  try {
    if (Array.isArray(output)) {
      return output.map((solutionData: any) => {
        if (solutionData && solutionData.label && Array.isArray(solutionData.facets)) {
          const { label, facets } = solutionData;

          const processedFacets = facets.map((facetData: Facet) => ({
            ...facetData,
            reduction: facetData.reduction ?? {
              solution: { positive: null, negative: null },
              facets: { positive: null, negative: null },
            },
            remaining: facetData.remaining ?? {
              solution: { positive: null, negative: null },
              facets: { positive: null, negative: null },
            },
            selectionState: facetData.selectionState ?? SelectionState.NotSelected,
          }));

          return { label, facets: processedFacets };
        } else {
          throw new Error('Invalid solution structure in the response');
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
