import React from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Plus, Loader2 } from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"
import { suggestWord } from '@/services/api' // API servisini import ediyoruz

interface WordSuggestion {
  english: string
  turkish: string
  example_sentence: string
  part_of_speech: string
}

const AddWordDialog: React.FC = () => {
  const [open, setOpen] = React.useState(false)
  const { toast } = useToast()

  const [formData, setFormData] = React.useState<WordSuggestion>({
    english: '',
    turkish: '',
    example_sentence: '',
    part_of_speech: 'noun'
  })

  const submitWordSuggestion = useMutation({
    mutationFn: (data: WordSuggestion) => suggestWord(data), // API servisini kullanıyoruz
    onSuccess: () => {
      setOpen(false)
      setFormData({
        english: '',
        turkish: '',
        example_sentence: '',
        part_of_speech: 'noun'
      })
      toast({
        title: "Word Suggested",
        description: "Your word suggestion has been submitted for review.",
      })
    },
    onError: (error: any) => {
      toast({
        variant: "destructive",
        title: "Error",
        description: error.response?.data?.detail || "Failed to submit word suggestion",
      })
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submitWordSuggestion.mutate(formData)
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Suggest New Word
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Suggest New Word</DialogTitle>
            <DialogDescription>
              Submit a new word for review. Once approved, it will be added to the learning system.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="english" className="text-right">
                English
              </Label>
              <Input
                id="english"
                name="english"
                value={formData.english}
                onChange={handleChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="turkish" className="text-right">
                Turkish
              </Label>
              <Input
                id="turkish"
                name="turkish"
                value={formData.turkish}
                onChange={handleChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="part_of_speech" className="text-right">
                Type
              </Label>
              <select
                id="part_of_speech"
                name="part_of_speech"
                value={formData.part_of_speech}
                onChange={handleChange}
                className="col-span-3 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="noun">Noun</option>
                <option value="verb">Verb</option>
                <option value="adjective">Adjective</option>
                <option value="adverb">Adverb</option>
                <option value="preposition">Preposition</option>
                <option value="conjunction">Conjunction</option>
                <option value="pronoun">Pronoun</option>
                <option value="interjection">Interjection</option>
              </select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="example_sentence" className="text-right">
                Example
              </Label>
              <Textarea
                id="example_sentence"
                name="example_sentence"
                value={formData.example_sentence}
                onChange={handleChange}
                placeholder="Enter an example sentence using this word"
                className="col-span-3"
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={submitWordSuggestion.isPending}>
              {submitWordSuggestion.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Submit for Review
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddWordDialog