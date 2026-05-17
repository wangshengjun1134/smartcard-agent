import { VectorChunk } from '../../types/file';

interface ChunkItemProps {
  chunk: VectorChunk;
  index: number;
}

/**
 * 向量分片项组件
 * 显示单个向量分片信息：ID、内容预览、位置、索引时间
 */
export function ChunkItem({ chunk, index }: ChunkItemProps) {
  return (
    <div className="chunk-item">
      {/* 分片标题 */}
      <div className="chunk-header">
        分片 #{index + 1}
        <span className="ml-2 text-[#999]">{chunk.indexedAt}</span>
      </div>

      {/* 内容预览 (最多 3 行) */}
      <div className="chunk-content">
        {chunk.content}
      </div>

      {/* 位置信息 */}
      <div className="chunk-position">
        位置: [{chunk.startPosition}, {chunk.endPosition}]
      </div>
    </div>
  );
}