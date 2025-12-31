// types/renderType.ts

export type ComponentType =
  | 'Root'
  | 'Section'
  | 'Container'
  | 'Grid'
  | 'Flex'
  | 'Card'
  | 'CardHeader'
  | 'CardContent'
  | 'CardFooter'
  | 'CardTitle'
  | 'CardDescription'
  | 'Text'
  | 'Button'
  | 'Input'
  | 'Textarea'
  | 'Label'
  | 'Image'
  | 'Badge'
  | 'Icon'
  | 'Separator'
  | 'Skeleton'
  | 'Link'
  | 'Link/A'
  | 'List'
  | 'ListItem'
  | 'Form'
  | 'Table'
  | 'TableRow'
  | 'TableCell'
  | 'TableHeader'
  | 'TableHead'
  | 'LineChart'
  | 'BarChart'
  | 'DonutChart'
  | 'PieChart'
  | 'AreaChart'
  | 'div'
  | 'span'
  | 'p'
  | 'div'
  | 'span'
  | 'p'
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'h5'
  | 'h6'
  | 'section'
  | 'main'
  | 'header'
  | 'footer'
  | 'nav'
  | 'aside'
  | 'article'
  | 'div'
  | 'span'
  | 'p'
  ;

export type TextTag =
  | 'p'
  | 'span'
  | 'label'
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'h5'
  | 'h6';

export interface SchemaProps {
  className?: string;
  id?: string;
  tag?: TextTag;
  src?: string;
  alt?: string;
  href?: string;
  target?: string;
  rel?: string;
  type?: string;
  placeholder?: string;
  defaultValue?: string;
  disabled?: boolean;
  required?: boolean;
  name?: string;
  htmlFor?: string;
  rows?: number;
  onClick?: () => void;
  onSubmit?: (e: React.FormEvent) => void;
  loading?: 'lazy' | 'eager';
  [key: string]: any; // Allow additional props
}

export interface SchemaNode {
  type: ComponentType;
  props?: SchemaProps;
  children?: (SchemaNode | string)[];
  content?: string;
  src?: string; // Legacy support
}

export interface SchemaValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

// Helper type guards
export function isSchemaNode(obj: any): obj is SchemaNode {
  return (
    obj &&
    typeof obj === 'object' &&
    'type' in obj &&
    typeof obj.type === 'string'
  );
}

export function isStringChild(child: any): child is string {
  return typeof child === 'string';
}

// Utility types for API responses
export interface GenerationResponse {
  success: boolean;
  project_id: string;
  project_title: string;
  project_description: string;
  generation_id: string;
  schema: SchemaNode;
  code: string;
  design_plan: DesignPlan;
  meta: GenerationMeta;
}

export interface DesignPlan {
  concept: string;
  theme: Theme;
  layout_plan: LayoutPlan;
  image_suggestions: ImageSuggestion[];
  design_system: DesignSystem;
}

export interface Theme {
  style: string;
  color_scheme: ColorScheme;
  typography: Typography;
  mood: string;
}

export interface ColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  danger?: string;
  background: string;
  surface: string;
  text: string;
  textSecondary?: string;
}

export interface Typography {
  heading: string;
  subheading: string;
  body: string;
  metric?: string;
}

export interface LayoutPlan {
  structure: string;
  header_section?: any;
  sections: LayoutSection[];
  responsive_strategy: string;
}

export interface LayoutSection {
  name: string;
  purpose: string;
  components: string[];
  layout?: string;
  spacing: string;
  background?: string;
  card_structure?: string;
}

export interface ImageSuggestion {
  location: string;
  description: string;
  alt_text: string;
  dimensions: string;
  placeholder_url: string;
}

export interface DesignSystem {
  spacing: string;
  radius: string;
  border_radius?: string;
  shadows: string;
  animations: string;
  grid: string;
}

export interface GenerationMeta {
  models: {
    planning: string;
    ui_generation: string;
  };
  usage: {
    planning: TokenUsage;
    generation: TokenUsage;
    total_tokens: number;
  };
}

export interface TokenUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}