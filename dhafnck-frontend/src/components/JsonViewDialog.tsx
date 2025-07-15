import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Copy, Check } from "lucide-react";

interface JsonViewDialogProps {
  title: string;
  data: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const JsonViewDialog: React.FC<JsonViewDialogProps> = ({ title, data, open, onOpenChange }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{title} - JSON View</span>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCopy}
              className="ml-4"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy
                </>
              )}
            </Button>
          </DialogTitle>
        </DialogHeader>
        <div className="overflow-auto">
          <pre className="bg-muted p-4 rounded-md text-sm">
            <code>{JSON.stringify(data, null, 2)}</code>
          </pre>
        </div>
      </DialogContent>
    </Dialog>
  );
};