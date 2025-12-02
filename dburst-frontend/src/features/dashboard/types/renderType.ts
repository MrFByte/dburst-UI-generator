export interface SchemaNode {
  type: string;
  props?: Record<string, any>;
  content?: string;
  children?: SchemaNode[];
  src?: string;
  metadata?: Record<string, any>;
}