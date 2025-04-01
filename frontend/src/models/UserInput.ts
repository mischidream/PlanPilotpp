import type { EncodingType } from "./EncodingType";

export interface UserInput {
    domainFile: string;
    problemFile: string;
    horizon: number;
    encoding: EncodingType;
  }
  