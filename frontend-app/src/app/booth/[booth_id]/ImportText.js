import {
	Dialog,
	DialogTrigger,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { NewspaperIcon } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { DropdownMenuItem } from "@radix-ui/react-dropdown-menu";

export default function ImportText() {
	const [textInput, setTextInput] = useState("");

	// TODO: Handle upload
	function handleUpload() {
		console.log(textInput);
	}

	return (
		<Dialog>
			<DialogTrigger
				className="flex gap-2 items-center text-sm ps-2 py-1 cursor-pointer"
				asChild
			>
				<DropdownMenuItem onSelect={e => e.preventDefault()}>
					<NewspaperIcon className="w-4 h-4" />
					From Plain Text
				</DropdownMenuItem>
			</DialogTrigger>
			<DialogContent onKeyDown={e => e.stopPropagation()}>
				<DialogHeader>
					<DialogTitle>Import from Text</DialogTitle>
					<DialogDescription>
						Paste the text you want to import
					</DialogDescription>
					<Textarea
						placeholder="Text to upload"
						value={textInput}
						onChange={e => setTextInput(e.target.value)}
					/>
					<Button onClick={handleUpload}>Upload</Button>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
