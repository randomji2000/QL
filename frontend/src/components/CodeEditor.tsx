import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

interface Props {
  value: string
  onChange?: (v: string) => void
  readOnly?: boolean
  height?: string
}

export default function CodeEditor({ value, onChange, readOnly = false, height = '100%' }: Props) {
  return (
    <div className="code-editor">
      <CodeMirror
        value={value}
        height={height}
        theme={oneDark}
        extensions={[python()]}
        onChange={onChange}
        readOnly={readOnly}
        basicSetup={{ foldGutter: false, autocompletion: false, highlightActiveLine: !readOnly }}
      />
    </div>
  )
}
