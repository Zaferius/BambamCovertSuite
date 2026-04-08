export type XhrResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

/**
 * POST a FormData body via XHR, reporting upload progress (0–100) via onProgress.
 */
export function xhrPost(
  url: string,
  body: FormData,
  onProgress: (pct: number) => void,
): Promise<XhrResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);

    const token = localStorage.getItem("bambam_token");
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      const text = xhr.responseText;
      resolve({
        ok: xhr.status >= 200 && xhr.status < 300,
        status: xhr.status,
        json: () => {
          try {
            return Promise.resolve(JSON.parse(text));
          } catch {
            return Promise.reject(new Error("Invalid JSON response"));
          }
        },
      });
    };

    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.onabort = () => reject(new Error("Upload aborted"));

    xhr.send(body);
  });
}

/**
 * Given N files and a total upload percentage (0–100),
 * distribute progress so files complete one by one, left to right.
 */
export function distributeProgress(
  files: { name: string }[],
  totalPct: number,
): { name: string; pct: number }[] {
  const n = files.length;
  if (n === 0) return [];

  return files.map((f, i) => {
    const sliceStart = (i / n) * 100;
    const sliceEnd = ((i + 1) / n) * 100;
    let pct: number;

    if (totalPct >= sliceEnd) {
      pct = 100;
    } else if (totalPct <= sliceStart) {
      pct = 0;
    } else {
      pct = Math.round(((totalPct - sliceStart) / (100 / n)));
    }

    return { name: f.name, pct };
  });
}
