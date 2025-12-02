export interface SchemaNode {
  type: string;
  props?: Record<string, any>;
  content?: string;
  children?: SchemaNode[];
  src?: string;
  metadata?: Record<string, any>;
}

export interface APIResponse {
  project_id: string;
  generation_id: string;
  schema: SchemaNode;
  code: string;
  meta: {
    provider: string;
    model?: string;
    usage: {
      total_tokens: number;
      prompt_tokens?: number;
      completion_tokens?: number;
    };
  };
}