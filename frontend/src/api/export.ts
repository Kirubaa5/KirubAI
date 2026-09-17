import { apiClient } from './client'
import { ExportFilterParams, ExportPreviewResponse, ExportFormat } from '@/types'

export const exportApi = {
  /**
   * Get real-time preview and statistics of matching words before exporting.
   */
  getPreview: async (params: ExportFilterParams = {}): Promise<ExportPreviewResponse> => {
    const response = await apiClient.get<ExportPreviewResponse>('/export/preview', { params })
    return response.data
  },

  /**
   * Download the generated export file (Anki deck, CSV spreadsheet, or JSON archive).
   */
  download: async (
    format: ExportFormat,
    params: ExportFilterParams = {}
  ): Promise<{ filename: string; success: boolean }> => {
    const endpoint = `/export/${format}`
    const response = await apiClient.get(endpoint, {
      params,
      responseType: 'blob',
    })

    // Extract filename from Content-Disposition header if present
    let filename = `kirubai_${format}_export`
    const ext = format === 'anki' ? 'txt' : format === 'csv' ? 'csv' : 'json'
    const disposition = response.headers['content-disposition'] || response.headers['Content-Disposition']

    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/i)
      if (match && match[1]) {
        filename = match[1]
      } else {
        filename = `${filename}.${ext}`
      }
    } else {
      filename = `${filename}.${ext}`
    }

    // Trigger browser file download
    const contentType = typeof response.headers['content-type'] === 'string'
      ? response.headers['content-type']
      : 'application/octet-stream'
    const blob = new Blob([response.data], {
      type: contentType,
    })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)

    return { filename, success: true }
  },
}
