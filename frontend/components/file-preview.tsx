"use client"

import { ScrollArea } from "@/components/ui/scroll-area"
import { FileCode2 } from "lucide-react"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"

interface FilePreviewProps {
  filePath: string | null
  content: string
  isLoading: boolean
  truncated?: boolean
}

const getLanguage = (fileName: string | null) => {
  if (!fileName) return "text"
  const ext = fileName.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'js':
    case 'jsx': return 'javascript'
    case 'ts':
    case 'tsx': return 'typescript'
    case 'py': return 'python'
    case 'html': return 'html'
    case 'css': return 'css'
    case 'json': return 'json'
    case 'md': return 'markdown'
    case 'sh': return 'bash'
    case 'yml':
    case 'yaml': return 'yaml'
    case 'go': return 'go'
    case 'rs': return 'rust'
    case 'java': return 'java'
    case 'c':
    case 'cpp':
    case 'h': return 'cpp'
    default: return 'text'
  }
}

export function FilePreview({ filePath, content, isLoading, truncated = false }: FilePreviewProps) {
  return (
    <div className="flex flex-col h-full bg-card">
      <div className="px-3 py-2 text-sm font-medium text-foreground flex items-center gap-2 border-b border-border flex-shrink-0">
        <FileCode2 className="h-4 w-4 text-muted-foreground" />
        <span className="truncate">{filePath ?? "File Preview (read-only)"}</span>
      </div>
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-3 py-2">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Loading file content...</div>
          ) : !filePath ? (
            <div className="text-sm text-muted-foreground">Click any file in Explorer to view read-only content.</div>
          ) : (
            <>
              {truncated && (
                <div className="text-xs text-muted-foreground mb-2">Preview truncated for large file.</div>
              )}
              <SyntaxHighlighter
                language={getLanguage(filePath)}
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  padding: 0,
                  background: "transparent",
                  fontSize: "12px",
                  lineHeight: "20px",
                }}
                wrapLines={true}
                wrapLongLines={true}
              >
                {content}
              </SyntaxHighlighter>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
