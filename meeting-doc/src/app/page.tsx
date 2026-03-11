"use client";

import React, { useEffect, useState } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Video,
  FileText,
  Search,
  Share,
  Download,
  Play,
  Clock,
  User,
  Sparkles,
  Bot,
  Loader2,
  AlertCircle,
  Youtube,
  Send,
} from "lucide-react";
import { getMeetings, fetchYoutubeTranscript } from "@/lib/api";
import { Meeting } from "@/types";

export default function MeetingDocApp() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetchingTranscript, setIsFetchingTranscript] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [fetchedTranscript, setFetchedTranscript] = useState<string | null>(null);
  const [transcriptMetadata, setTranscriptMetadata] = useState<{
    video_id: string;
    word_count: number;
  } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const meetingList = await getMeetings();
        setMeetings(meetingList);
      } catch (err) {
        console.error("Failed to fetch meetings:", err);
        setError("Unable to connect to the backend. Please ensure the Django server is running at http://127.0.0.1:8000");
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const handleFetchTranscript = async () => {
    if (!youtubeUrl) return;
    try {
      setIsFetchingTranscript(true);
      setError(null);
      const result = await fetchYoutubeTranscript(youtubeUrl);
      setFetchedTranscript(result.transcript_text);
      setTranscriptMetadata({
        video_id: result.video_id,
        word_count: result.word_count,
      });
    } catch (err: any) {
      console.error("Failed to fetch transcript:", err);
      setError(err.message || "Failed to fetch transcript from YouTube.");
    } finally {
      setIsFetchingTranscript(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-zinc-400">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-indigo-500" />
          <p className="text-sm font-medium animate-pulse">Connecting to Knowledge Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-zinc-950 font-sans text-zinc-50 overflow-hidden">
      {/* Header */}
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-950/50 px-6 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 shadow-inner">
            <Video className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-100">Meeting-Doc</h1>
            <p className="text-xs font-medium text-zinc-400">Knowledge Asset Extractor</p>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-10">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <Input
              type="text"
              placeholder="Search in transcript, summaries, and action items..."
              className="h-10 w-full rounded-full border-zinc-800 bg-zinc-900/50 pl-10 text-sm text-zinc-200 placeholder:text-zinc-500 focus-visible:ring-indigo-500/50"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger
                className="h-10 w-10 cursor-pointer rounded-full border border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-white inline-flex items-center justify-center"
              >
                <Share className="h-4 w-4" />
              </TooltipTrigger>
              <TooltipContent className="bg-zinc-800 text-zinc-200 border-zinc-700">Share Asset</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Button className="h-10 gap-2 rounded-full bg-indigo-600 px-5 text-sm font-semibold text-white shadow hover:bg-indigo-700">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export to Confluence</span>
          </Button>

          <Separator orientation="vertical" className="h-8 bg-zinc-800 mx-2" />

          <Avatar className="h-9 w-9 border border-zinc-800 cursor-pointer">
            <AvatarImage src="https://github.com/shadcn.png" alt="@user" />
            <AvatarFallback className="bg-zinc-800">U</AvatarFallback>
          </Avatar>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full">

          {/* Left Panel: YouTube Input & Video Preview */}
          <ResizablePanel defaultSize={45} minSize={30} className="flex flex-col bg-zinc-950">
            <ScrollArea className="flex-1 p-6">
              
              {/* YouTube Input Section */}
              <Card className="mb-8 border-zinc-800 bg-zinc-900/50 shadow-lg">
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                    <Youtube className="h-5 w-5 text-red-500" />
                    Process YouTube Meeting
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="Paste YouTube URL here..."
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                      className="h-11 border-zinc-700 bg-zinc-950/50 text-zinc-200 focus-visible:ring-indigo-500/50"
                    />
                    <Button 
                      onClick={handleFetchTranscript}
                      disabled={isFetchingTranscript || !youtubeUrl}
                      className="h-11 bg-indigo-600 hover:bg-indigo-700 text-white min-w-[140px] shadow-indigo-500/10 shadow-lg"
                    >
                      {isFetchingTranscript ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Send className="h-4 w-4 mr-2" />
                      )}
                      Fetch 
                    </Button>
                  </div>
                  
                  {transcriptMetadata && (
                    <div className="flex gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
                      <Badge variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400 py-1">
                        Video ID: {transcriptMetadata.video_id}
                      </Badge>
                      <Badge variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400 py-1">
                        {transcriptMetadata.word_count} words
                      </Badge>
                    </div>
                  )}

                  {error && (
                    <div className="flex items-center gap-2 text-rose-400 text-sm mt-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <p>{error}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Video Player Placeholder / Preview */}
              <div className="group relative aspect-video w-full overflow-hidden rounded-2xl border border-zinc-800 bg-black shadow-2xl transition-all duration-300 hover:border-zinc-700">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={transcriptMetadata ? `https://img.youtube.com/vi/${transcriptMetadata.video_id}/maxresdefault.jpg` : "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop"}
                  alt="Meeting Preview"
                  className="h-full w-full object-cover opacity-50 transition-opacity duration-500 group-hover:opacity-30"
                />

                <div className="absolute inset-0 flex items-center justify-center pb-8">
                  <div className="flex h-16 w-16 cursor-pointer items-center justify-center rounded-full bg-indigo-600/90 text-white shadow-lg backdrop-blur hover:bg-indigo-600 hover:scale-105 transition-all">
                    <Play className="h-6 w-6 ml-1" />
                  </div>
                </div>

                <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/90 to-transparent p-4 pt-12">
                   <div className="flex items-center justify-between text-xs font-semibold text-zinc-400">
                    <span className="flex items-center gap-1.5"><Clock className="h-3 w-3" /> Ready for processing</span>
                    <span>HD 1080p</span>
                  </div>
                </div>
              </div>

              {/* Detected Context Visuals */}
              <div className="mt-8">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="h-5 w-5 text-amber-500" />
                  <h3 className="text-lg font-semibold tracking-tight text-zinc-100">Detected Context (AI)</h3>
                </div>

                <div className="grid grid-cols-2 gap-4 opacity-50">
                  <Card className="border-zinc-800 bg-zinc-900/40 cursor-not-allowed">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                        <span className="p-1.5 rounded-md bg-blue-500/10 text-blue-400"><FileText className="w-3.5 h-3.5" /></span>
                        Architecture Diagram
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-20 w-full bg-zinc-800/30 rounded-md flex items-center justify-center">
                        <Bot className="h-6 w-6 text-zinc-700" />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-600">
                        <span>Analysis Pending</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-zinc-800 bg-zinc-900/40 cursor-not-allowed">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                        <span className="p-1.5 rounded-md bg-green-500/10 text-green-400"><CodeIcon className="w-3.5 h-3.5" /></span>
                        Code Walkthrough
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-20 w-full bg-zinc-800/30 rounded-md flex items-center justify-center font-mono text-[8px] text-zinc-700">
                        PROCESSING...
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-600">
                        <span>Analysis Pending</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

            </ScrollArea>
          </ResizablePanel>

          <ResizableHandle className="w-1.5 bg-zinc-900 hover:bg-indigo-500/50 transition-colors" withHandle />

          {/* Right Panel: Documentation Tabs */}
          <ResizablePanel defaultSize={55} minSize={30} className="flex flex-col bg-[#09090b]">
            <Tabs defaultValue="transcript" className="flex h-full flex-col">

              <div className="flex border-b border-zinc-800 bg-zinc-950/80 px-4 pt-4">
                <TabsList className="bg-zinc-900/50 border border-zinc-800 mb-0 h-10 w-auto rounded-t-lg rounded-b-none p-1 pb-0">
                  <TabsTrigger
                    value="summary"
                    className="data-[state=active]:bg-zinc-800 data-[state=active]:text-indigo-300 rounded-md rounded-b-none px-6 transition-all"
                  >
                    Clean Summary
                  </TabsTrigger>
                  <TabsTrigger
                    value="action-items"
                    className="data-[state=active]:bg-zinc-800 data-[state=active]:text-indigo-300 rounded-md rounded-b-none px-6 transition-all"
                  >
                    Action Items
                  </TabsTrigger>
                  <TabsTrigger
                    value="transcript"
                    className="data-[state=active]:bg-zinc-800 data-[state=active]:text-indigo-300 rounded-md rounded-b-none px-6 transition-all"
                  >
                    Raw Transcript
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* tab contents */}
              <ScrollArea className="flex-1 bg-zinc-900/20 p-6">

                <TabsContent value="summary" className="m-0 space-y-6 data-[state=inactive]:hidden focus-visible:outline-none focus-visible:ring-0">
                  <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                    <div className="h-16 w-16 rounded-full bg-indigo-500/10 flex items-center justify-center">
                       <Bot className="h-8 w-8 text-indigo-400" />
                    </div>
                    <div className="space-y-2">
                       <h3 className="text-xl font-bold text-white">Analysis Required</h3>
                       <p className="text-zinc-400 max-w-xs mx-auto text-sm">Fetch a transcript first, then AI will generate a structured summary of the meeting.</p>
                    </div>
                    <Button variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400" disabled>
                      Generate Summary
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="action-items" className="m-0 space-y-4 data-[state=inactive]:hidden focus-visible:outline-none focus-visible:ring-0">
                   <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                    <div className="h-16 w-16 rounded-full bg-indigo-500/10 flex items-center justify-center">
                       <Checkbox className="h-6 w-6 border-indigo-400 text-indigo-400" disabled />
                    </div>
                    <div className="space-y-2">
                       <h3 className="text-xl font-bold text-white">No Action Items</h3>
                       <p className="text-zinc-400 max-w-xs mx-auto text-sm">Action items will be automatically extracted during the AI processing phase.</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="transcript" className="m-0 data-[state=inactive]:hidden focus-visible:outline-none focus-visible:ring-0">
                  <div className="space-y-6">
                    {fetchedTranscript ? (
                      <div className="bg-zinc-900/40 border border-zinc-800/50 p-6 rounded-2xl animate-in fade-in duration-500">
                        <div className="flex items-center justify-between mb-4">
                           <div className="flex items-center gap-2">
                              <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-[10px] font-bold">YT</div>
                              <span className="text-sm font-medium text-indigo-300">YouTube Transcript</span>
                           </div>
                           <Badge variant="outline" className="text-[10px] border-zinc-800 text-zinc-500 italic">Raw Data</Badge>
                        </div>
                        <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap">
                          {fetchedTranscript}
                        </p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-20 text-center space-y-4 opacity-50">
                        <div className="h-16 w-16 rounded-full bg-zinc-800 flex items-center justify-center">
                           <FileText className="h-8 w-8 text-zinc-500" />
                        </div>
                        <div className="space-y-2">
                           <h3 className="text-lg font-semibold text-zinc-400">Transcript Empty</h3>
                           <p className="text-zinc-500 max-w-xs mx-auto text-sm italic">Pasting a YouTube URL above will populate this section with real-time text extraction.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

              </ScrollArea>
            </Tabs>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>
    </div>
  );
}

function CodeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
}