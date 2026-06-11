import { useState, useEffect, useCallback } from 'react';
import { KnowledgeBase } from '../types/knowledge';
import { getApiUrl } from '../config/api';

interface UseKnowledgeBasesReturn {
  knowledgeBases: KnowledgeBase[];
  loading: boolean;
  error: Error | null;
  refresh: () => void;
}

/**
 * 知识库列表 Hook
 */
export function useKnowledgeBases(): UseKnowledgeBasesReturn {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchKnowledgeBases = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(getApiUrl('/api/knowledge-bases/list'));

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch knowledge bases: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Knowledge bases API response:', data);

      if (data.status === 'ok' && Array.isArray(data.data)) {
        setKnowledgeBases(data.data as KnowledgeBase[]);
      } else {
        console.warn('Invalid API response format:', data);
        setKnowledgeBases([]);
      }
    } catch (err) {
      console.error('Fetch knowledge bases failed:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch knowledge bases'));
      setKnowledgeBases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKnowledgeBases();
  }, [fetchKnowledgeBases]);

  return {
    knowledgeBases,
    loading,
    error,
    refresh: fetchKnowledgeBases,
  };
}
