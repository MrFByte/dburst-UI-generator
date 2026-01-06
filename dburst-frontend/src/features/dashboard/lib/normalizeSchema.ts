export function normalizeSchema(node: any): any {
  if (!node) return node;

  // Deep clone to avoid mutating frozen/immutable objects
  node = JSON.parse(JSON.stringify(node));

  // Migrate legacy 'class' to 'props.className'
  if (node.class && !node.props?.className) {
    if (!node.props) node.props = {};
    node.props.className = node.class;
    delete node.class;
  }

  // Ensure props object exists
  if (!node.props) node.props = {};

  // Type-specific normalizations
  switch (node.type) {
    case 'Text':
      // Ensure text has proper color if not specified
      if (!node.props.className?.includes('text-')) {
        node.props.className = `${node.props.className || ''} text-gray-900`.trim();
      }
      break;

    case 'Flex':
      // CRITICAL: Ensure Flex always has flex class
      if (!node.props.className?.includes('flex')) {
        node.props.className = `flex ${node.props.className || ''}`.trim();
      }
      break;

    case 'Card':
      // Ensure Card has base styles
      if (!node.props.className?.includes('rounded')) {
        node.props.className = `${node.props.className || ''} bg-white rounded-lg border shadow-sm`.trim();
      }
      break;

    case 'CardHeader':
      // Ensure CardHeader has proper padding
      if (!node.props.className?.includes('p-')) {
        node.props.className = `${node.props.className || ''} p-6`.trim();
      }
      break;

    case 'CardContent':
      // Ensure CardContent has proper padding
      if (!node.props.className?.includes('p-')) {
        node.props.className = `${node.props.className || ''} p-6 pt-0`.trim();
      }
      break;

    case 'CardTitle':
      // Ensure CardTitle has proper font size
      if (!node.props.className?.includes('text-')) {
        node.props.className = `${node.props.className || ''} text-lg font-semibold`.trim();
      }
      break;

    case 'CardDescription':
      // Ensure CardDescription has muted color
      if (!node.props.className?.includes('text-')) {
        node.props.className = `${node.props.className || ''} text-sm text-gray-500`.trim();
      }
      break;

    case 'Button':
      // Ensure buttons have proper base styles
      if (!node.props.className?.includes('px-') && !node.props.className?.includes('py-')) {
        node.props.className = `${node.props.className || ''} px-4 py-2 rounded-md transition-colors`.trim();
      }
      break;

    case 'Badge':
      // Ensure badges have proper base styles
      if (!node.props.className?.includes('rounded')) {
        node.props.className = `${node.props.className || ''} inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold`.trim();
      }
      break;

    case 'Input':
    case 'Textarea':
      // Ensure form inputs have proper styles
      if (!node.props.className?.includes('border')) {
        node.props.className = `${node.props.className || ''} border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500`.trim();
      }
      break;

    case 'Separator':
      // Ensure separator has proper border
      if (!node.props.className?.includes('border')) {
        node.props.className = `${node.props.className || ''} border-t border-gray-200 my-4`.trim();
      }
      break;
  }

  // Ensure white backgrounds have dark text
  if (
    node.props.className?.includes('bg-white') &&
    !node.props.className.includes('text-')
  ) {
    node.props.className = `${node.props.className} text-gray-900`;
  }

  // Recursively normalize children
  if (node.children && Array.isArray(node.children)) {
    node.children = node.children.map((child: any) => {
      // Skip string children
      if (typeof child === 'string') return child;
      return normalizeSchema(child);
    });
  }

  return node;
}

// Helper function to validate schema structure
export function validateSchemaStructure(node: any): boolean {
  if (!node) return false;

  // Must have a type
  if (!node.type) {
    console.error('Schema node missing type:', node);
    return false;
  }

  // Props must be an object if present
  if (node.props && typeof node.props !== 'object') {
    console.error('Schema node props must be an object:', node);
    return false;
  }

  // Children must be an array if present
  if (node.children && !Array.isArray(node.children)) {
    console.error('Schema node children must be an array:', node);
    return false;
  }

  // Recursively validate children
  if (node.children && Array.isArray(node.children)) {
    for (const child of node.children) {
      if (typeof child === 'string') continue; // String children are allowed
      if (!validateSchemaStructure(child)) return false;
    }
  }

  return true;
}

// Helper to fix common schema issues
export function repairSchema(node: any): any {
  if (!node) return node;

  // Fix missing type
  if (!node.type) {
    if (node.content) {
      node.type = 'Text';
    } else if (node.children) {
      node.type = 'Container';
    } else {
      node.type = 'div';
    }
  }

  // Fix children that should be content
  if (node.children && node.children.length === 1 && typeof node.children[0] === 'string') {
    node.content = node.children[0];
    delete node.children;
  }

  // Normalize and validate
  node = normalizeSchema(node);

  return node;
}