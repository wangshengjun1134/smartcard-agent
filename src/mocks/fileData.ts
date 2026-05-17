import { FileNode, FileDetail, VectorChunk } from '../types/file';

/**
 * 模拟文件结构数据
 */
export const mockFileStructure: FileNode[] = [
  {
    id: 'folder-1',
    name: '智能卡规范',
    type: 'folder',
    path: '/docs/智能卡规范',
    isFolder: true,
    children: [
      {
        id: 'file-1',
        name: 'ISO7816.pdf',
        type: 'pdf',
        path: '/docs/智能卡规范/ISO7816.pdf',
        isFolder: false,
        size: 2500000,
        createdAt: '2025-01-15',
        modifiedAt: '2025-01-20',
      },
      {
        id: 'file-2',
        name: 'ISO14443.pdf',
        type: 'pdf',
        path: '/docs/智能卡规范/ISO14443.pdf',
        isFolder: false,
        size: 1800000,
        createdAt: '2025-01-16',
        modifiedAt: '2025-01-18',
      },
      {
        id: 'file-3',
        name: '智能卡开发指南.md',
        type: 'markdown',
        path: '/docs/智能卡规范/智能卡开发指南.md',
        isFolder: false,
        size: 50000,
        createdAt: '2025-01-10',
        modifiedAt: '2025-01-22',
      },
    ],
  },
  {
    id: 'folder-2',
    name: '项目文档',
    type: 'folder',
    path: '/docs/项目文档',
    isFolder: true,
    children: [
      {
        id: 'file-4',
        name: '需求规格说明书.docx',
        type: 'word',
        path: '/docs/项目文档/需求规格说明书.docx',
        isFolder: false,
        size: 350000,
        createdAt: '2025-01-08',
        modifiedAt: '2025-01-12',
      },
      {
        id: 'file-5',
        name: '架构设计文档.md',
        type: 'markdown',
        path: '/docs/项目文档/架构设计文档.md',
        isFolder: false,
        size: 80000,
        createdAt: '2025-01-09',
        modifiedAt: '2025-01-15',
      },
      {
        id: 'folder-3',
        name: '测试报告',
        type: 'folder',
        path: '/docs/项目文档/测试报告',
        isFolder: true,
        children: [
          {
            id: 'file-6',
            name: '单元测试报告.pdf',
            type: 'pdf',
            path: '/docs/项目文档/测试报告/单元测试报告.pdf',
            isFolder: false,
            size: 450000,
            createdAt: '2025-01-18',
            modifiedAt: '2025-01-19',
          },
          {
            id: 'file-7',
            name: '集成测试报告.pdf',
            type: 'pdf',
            path: '/docs/项目文档/测试报告/集成测试报告.pdf',
            isFolder: false,
            size: 620000,
            createdAt: '2025-01-19',
            modifiedAt: '2025-01-21',
          },
        ],
      },
    ],
  },
  {
    id: 'folder-4',
    name: '参考资料',
    type: 'folder',
    path: '/docs/参考资料',
    isFolder: true,
    children: [
      {
        id: 'file-8',
        name: '密码学基础.pdf',
        type: 'pdf',
        path: '/docs/参考资料/密码学基础.pdf',
        isFolder: false,
        size: 5200000,
        createdAt: '2025-01-05',
        modifiedAt: '2025-01-10',
      },
      {
        id: 'file-9',
        name: 'JavaCard白皮书.pdf',
        type: 'pdf',
        path: '/docs/参考资料/JavaCard白皮书.pdf',
        isFolder: false,
        size: 3100000,
        createdAt: '2025-01-06',
        modifiedAt: '2025-01-08',
      },
      {
        id: 'file-10',
        name: 'APDU命令速查.txt',
        type: 'text',
        path: '/docs/参考资料/APDU命令速查.txt',
        isFolder: false,
        size: 15000,
        createdAt: '2025-01-11',
        modifiedAt: '2025-01-23',
      },
    ],
  },
];

/**
 * 模拟向量分片数据生成器
 */
function generateMockChunks(fileId: string): VectorChunk[] {
  const chunkCount = Math.floor(Math.random() * 15) + 5; // 5-20个分片
  const chunks: VectorChunk[] = [];

  const sampleContents = [
    'ISO/IEC 7816 是智能卡的国际标准，定义了智能卡的物理特性、电气接口、传输协议和应用协议。该标准由多个部分组成，每个部分涵盖不同的技术领域...',
    '智能卡是一种包含嵌入式微处理器的卡片，能够存储和处理数据。它广泛应用于金融、电信、交通、医疗等领域...',
    'APDU (Application Protocol Data Unit) 是智能卡应用层通信的数据单元格式。APDU 命令由头部和可选的数据体组成...',
    'JavaCard 技术允许在智能卡上运行 Java 应用程序。JavaCard API 提供了面向对象的编程接口，简化了智能卡应用开发...',
    '非接触式智能卡使用射频技术进行通信，遵循 ISO 14443 标准。卡片和读卡器通过电磁场进行数据交换...',
  ];

  for (let i = 0; i < chunkCount; i++) {
    const contentIndex = i % sampleContents.length;
    const startPosition = i * 500;
    const endPosition = startPosition + 500;

    chunks.push({
      id: `${fileId}-chunk-${i + 1}`,
      content: sampleContents[contentIndex],
      startPosition,
      endPosition,
      indexedAt: '2025-01-16',
    });
  }

  return chunks;
}

/**
 * 模拟文件详情数据
 */
export function getMockFileDetail(fileId: string): FileDetail | null {
  // 在文件结构中查找文件
  const findFile = (nodes: FileNode[]): FileNode | null => {
    for (const node of nodes) {
      if (node.id === fileId) return node;
      if (node.children) {
        const found = findFile(node.children);
        if (found) return found;
      }
    }
    return null;
  };

  const file = findFile(mockFileStructure);
  if (!file || file.isFolder) return null;

  return {
    ...file,
    indexed: true,
    chunkCount: Math.floor(Math.random() * 15) + 5,
    chunks: generateMockChunks(fileId),
  };
}

/**
 * 模拟 API 延迟
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}