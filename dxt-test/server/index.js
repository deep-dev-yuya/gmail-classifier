#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import fs from 'fs/promises';
import path from 'path';

// DXT File Manager Server for Gmail Classifier
class GmailClassifierFileManager {
  constructor() {
    this.server = new Server({
      name: 'gmail-classifier-file-manager',
      version: '1.0.0',
      description: 'File manager for Gmail Classifier project'
    });
    
    this.workspaceDir = process.env.WORKSPACE || '/Users/hasegawayuya/Projects/dev-projects/gmail-classifier';
    this.debugMode = process.env.DEBUG === 'true';
    
    this.setupHandlers();
  }

  setupHandlers() {
    // List tools
    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: [
          {
            name: 'read_file',
            description: 'Read a file from the Gmail Classifier workspace',
            inputSchema: {
              type: 'object',
              properties: {
                file_path: {
                  type: 'string',
                  description: 'Relative path to the file within the workspace'
                }
              },
              required: ['file_path']
            }
          },
          {
            name: 'write_file',
            description: 'Write content to a file in the Gmail Classifier workspace',
            inputSchema: {
              type: 'object',
              properties: {
                file_path: {
                  type: 'string',
                  description: 'Relative path to the file within the workspace'
                },
                content: {
                  type: 'string',
                  description: 'Content to write to the file'
                }
              },
              required: ['file_path', 'content']
            }
          },
          {
            name: 'list_files',
            description: 'List files in a directory within the Gmail Classifier workspace',
            inputSchema: {
              type: 'object',
              properties: {
                directory_path: {
                  type: 'string',
                  description: 'Relative path to the directory within the workspace',
                  default: '.'
                }
              }
            }
          },
          {
            name: 'get_workspace_info',
            description: 'Get information about the current workspace',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      if (this.debugMode) {
        console.error(`[DXT] Tool call: ${name}`, args);
      }

      try {
        switch (name) {
          case 'read_file':
            return await this.readFile(args.file_path);
          case 'write_file':
            return await this.writeFile(args.file_path, args.content);
          case 'list_files':
            return await this.listFiles(args.directory_path || '.');
          case 'get_workspace_info':
            return await this.getWorkspaceInfo();
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`
            }
          ]
        };
      }
    });
  }

  async readFile(filePath) {
    const fullPath = path.join(this.workspaceDir, filePath);
    
    // Security check: ensure file is within workspace
    if (!fullPath.startsWith(this.workspaceDir)) {
      throw new Error('Access denied: File is outside workspace');
    }
    
    try {
      const content = await fs.readFile(fullPath, 'utf8');
      return {
        content: [
          {
            type: 'text',
            text: content
          }
        ]
      };
    } catch (error) {
      throw new Error(`Failed to read file: ${error.message}`);
    }
  }

  async writeFile(filePath, content) {
    const fullPath = path.join(this.workspaceDir, filePath);
    
    // Security check: ensure file is within workspace
    if (!fullPath.startsWith(this.workspaceDir)) {
      throw new Error('Access denied: File is outside workspace');
    }
    
    try {
      // Create directory if it doesn't exist
      await fs.mkdir(path.dirname(fullPath), { recursive: true });
      await fs.writeFile(fullPath, content, 'utf8');
      
      return {
        content: [
          {
            type: 'text',
            text: `File written successfully: ${filePath}`
          }
        ]
      };
    } catch (error) {
      throw new Error(`Failed to write file: ${error.message}`);
    }
  }

  async listFiles(dirPath) {
    const fullPath = path.join(this.workspaceDir, dirPath);
    
    // Security check: ensure directory is within workspace
    if (!fullPath.startsWith(this.workspaceDir)) {
      throw new Error('Access denied: Directory is outside workspace');
    }
    
    try {
      const files = await fs.readdir(fullPath, { withFileTypes: true });
      const fileList = files.map(file => ({
        name: file.name,
        type: file.isDirectory() ? 'directory' : 'file',
        path: path.join(dirPath, file.name)
      }));
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(fileList, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Failed to list files: ${error.message}`);
    }
  }

  async getWorkspaceInfo() {
    try {
      const stats = await fs.stat(this.workspaceDir);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              workspace_directory: this.workspaceDir,
              debug_mode: this.debugMode,
              directory_exists: stats.isDirectory(),
              created_at: stats.birthtime,
              modified_at: stats.mtime
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Failed to get workspace info: ${error.message}`);
    }
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    if (this.debugMode) {
      console.error('[DXT] Gmail Classifier File Manager started');
      console.error(`[DXT] Workspace: ${this.workspaceDir}`);
    }
  }
}

// Start the server
const server = new GmailClassifierFileManager();
server.start().catch(error => {
  console.error('[DXT] Server error:', error);
  process.exit(1);
});