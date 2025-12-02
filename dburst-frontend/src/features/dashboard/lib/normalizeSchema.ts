export function normalizeSchema(node: any): any {
  if (!node) return node;

  if (node.class && !node.props?.className) {
    if (!node.props) node.props = {};
    node.props.className = node.class;
    delete node.class;
  }

  if (node.type === 'Text' && !node.props?.className?.includes('text-')) {
    node.props = node.props || {};
    node.props.className = `${node.props.className || ''} text-gray-900`.trim();
  }

  if (node.type === 'Card' && !node.props?.className?.includes('flex')) {
    node.props = node.props || {};
    node.props.className = `${node.props.className || ''} flex flex-col gap-3`.trim();
  }

  if (
    node.props?.className?.includes('bg-white') &&
    !node.props.className.includes('text-')
  ) {
    node.props.className = `${node.props.className} text-gray-900`;
  }

  if (node.children && Array.isArray(node.children)) {
    node.children = node.children.map((child: any) => normalizeSchema(child));
  }

  return node;
}