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
import useSourcesStore from "@/stores/useSourcesStore";
import { DialogClose } from "@radix-ui/react-dialog";

export default function ImportText() {
	const [textInput, setTextInput] = useState("");
	const addSource = useSourcesStore(state => state.addSource);

	// TODO: Handle upload
	function handleUpload() {
		if (!textInput) return;
		console.log("Uploading text...", textInput);

		setTextInput("");
		setTimeout(() => {
			addSource({
				name: "Text at " + new Date().toLocaleString().split(", ")[1],
				summary: textInput,
			});
		}, 2000);
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
					<DialogClose asChild>
						<Button onClick={handleUpload}>Upload</Button>
					</DialogClose>
				</DialogHeader>
			</DialogContent>
		</Dialog>
	);
}
