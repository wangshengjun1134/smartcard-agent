import { FileDetail } from '../../types/file';
import { ChunkItem } from './ChunkItem';

interface VectorChunksListProps {
  detail: FileDetail;
}

/**
 * 向量分片列表组件
 * 显示分片数量和分片列表
 */
export function VectorChunksList({ detail }: VectorChunksListProps) {
  return (
    <div className="info-section">
      <div className="section-title">
        向量数据库分片
        <span className="ml-2 text-[#999] text-xs">
          分片数量: {detail.chunkCount}
        </span>
      </div>

      {/* 索引状态 */}
      <div className="info-item">
        <div className="info-label">索引状态</div>
        <div className="info-value">
          {detail.indexed ? (
            <span className="text-[#10b981]">已索引 ✓</span>
          ) : (
            <span className="text-[#ff4d4f]">未索引</span>
          )}
        </div>
      </div>

      {/* 分片列表 */}
      {detail.indexed && detail.chunks.length > 0 ? (
        <div className="chunk-list">
          {detail.chunks.map((chunk, index) => (
            <ChunkItem key={chunk.id} chunk={chunk} index={index} />
          ))}
        </div>
      ) : (
        <div className="text-[#999] text-sm text-center py-4">
          {detail.indexed ? '暂无分片数据' : '文件尚未进行向量索引'}
        </div>
      )}
    </div>
  );
}