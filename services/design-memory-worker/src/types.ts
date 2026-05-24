export interface Env {
  DESIGN_KV: KVNamespace;
  NVIDIA_API_KEY: string;
  ADMIN_TOKEN?: string;
  NVIDIA_BASE_URL?: string;
}

export interface NvidiaModel {
  id: string;
  object?: string;
  owned_by?: string;
  root?: string;
  parent?: string | null;
  [key: string]: unknown;
}

export interface SelectedEmbeddingModel {
  id: string;
  modality: "multimodal" | "image" | "text";
  score: number;
  reason: string;
}

export interface DesignAssetRecord {
  sha256: string;
  path: string;
  name: string;
  source: "generated" | "reference" | "unknown";
  brand?: string;
  project?: string;
  assetId?: string;
  width?: number;
  height?: number;
  aspect?: string;
  prompt?: string;
  caption?: string;
  tags?: string[];
  flows?: string[];
  colors?: string[];
  imageDataUri?: string;
  createdAt?: string;
}

export interface StoredAssetRecord extends Omit<DesignAssetRecord, "imageDataUri"> {
  embeddingModel: string;
  embeddingModality: SelectedEmbeddingModel["modality"];
  updatedAt: string;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  brand?: string;
  aspect?: string;
  flow?: string;
}

export interface SearchResult {
  score: number;
  asset: StoredAssetRecord;
}

export interface StoredVector {
  sha256: string;
  vector: number[];
}
