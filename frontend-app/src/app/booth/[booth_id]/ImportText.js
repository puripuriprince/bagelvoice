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

		// Call the new backend endpoint
		fetch("http://localhost:8080/summarize-text", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				text: textInput,
			}),
		})
			.then(response => {
				if (!response.ok) {
					throw new Error("Network response was not ok");
				}
				return response.json();
			})
			.then(data => {
				// Add the summarized text to your sources
				addSource({
					id: data.id,
					name: data.name,
					summary: data.summary,
				});

				setTextInput(""); // Clear the input field
			})
			.catch(error => {
				console.error("Error:", error);
			});
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
