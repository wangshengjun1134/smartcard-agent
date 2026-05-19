/**
 * 计算文件的哈希值
 * 使用 SHA-256 算法
 */

/**
 * 计算文件的 SHA-256 哈希值
 * @param file 要计算哈希的文件
 * @returns 哈希值字符串
 */
export async function calculateFileHash(file: File): Promise<string> {
  // 读取文件内容
  const buffer = await file.arrayBuffer();

  // 使用 Web Crypto API 计算 SHA-256
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);

  // 将哈希值转换为十六进制字符串
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return hashHex;
}