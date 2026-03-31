"""Foil generator for Programisto.

Requirement 4: Foil Generation

Generates coding patterns and templates appropriate for web development.
Detects TypeScript and includes TypeScript patterns when appropriate.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from scanner.project_scanner import ProjectStructure


@dataclass
class Foil:
    """A coding foil (pattern/template)."""

    id: str
    name: str
    description: str
    language: str
    content: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    file_path: str = ""
    is_typescript: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "file_path": self.file_path,
            "is_typescript": self.is_typescript,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
        }


class FoilGenerator:
    """Generates Foils for web development."""

    # Built-in Foils templates
    FOIL_TEMPLATES = {
        "base-component": {
            "name": "Base Component",
            "description": "A reusable base component with common props and lifecycle",
            "language": "typescript",
            "is_typescript": True,
        },
        "custom-hook": {
            "name": "Custom Hook",
            "description": "A reusable custom hook for state management",
            "language": "typescript",
            "is_typescript": True,
        },
        "api-client": {
            "name": "API Client",
            "description": "Type-safe API client with interceptors",
            "language": "typescript",
            "is_typescript": True,
        },
        "validation-schema": {
            "name": "Validation Schema",
            "description": "Zod validation schema for forms",
            "language": "typescript",
            "is_typescript": True,
        },
        "react-context": {
            "name": "React Context",
            "description": "React context provider pattern",
            "language": "typescript",
            "is_typescript": True,
        },
        "css-module": {
            "name": "CSS Module",
            "description": "Scoped CSS module",
            "language": "css",
            "is_typescript": False,
        },
        "webpack-config": {
            "name": "Webpack Config",
            "description": "Webpack configuration template",
            "language": "javascript",
            "is_typescript": False,
        },
    }

    def __init__(self, project_structure: Optional[ProjectStructure] = None):
        """Initialize the foil generator.

        Args:
            project_structure: Optional project structure for context.
        """
        self.project_structure = project_structure
        self.foils: Dict[str, Foil] = {}
        self._load_built_in_foils()

    def _load_built_in_foils(self) -> None:
        """Load built-in foil templates."""
        # Base Component Foil
        self.foils["base-component"] = Foil(
            id="base-component",
            **self.FOIL_TEMPLATES["base-component"],
            content="""import React, { ReactNode, HTMLAttributes, ReactHTML } from 'react';

interface BaseComponentProps<T extends keyof ReactHTML = 'div'> {
  as?: T;
  children?: ReactNode;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  [key: string]: any;
}

export function BaseComponent<T extends keyof ReactHTML = 'div'>({
  as: Tag = 'div' as T,
  children,
  className = '',
  disabled = false,
  loading = false,
  ...props
}: BaseComponentProps<T>) {
  if (loading) {
    return <span className="loading-spinner" />;
  }

  return (
    <Tag
      className={`base-component ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </Tag>
  );
}

export default BaseComponent;
""",
            tags=["component", "base", "react", "typescript"],
            dependencies=["react"],
            file_path="src/components/BaseComponent.tsx",
        )

        # Custom Hook Foil
        self.foils["custom-hook"] = Foil(
            id="custom-hook",
            **self.FOIL_TEMPLATES["custom-hook"],
            content="""import { useState, useCallback, useEffect } from 'react';

interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useAsyncState<T>(
  initialData: T | null = null,
  refetchFn: () => Promise<T>
): UseAsyncState<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await refetchFn();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [refetchFn]);

  return { data, loading, error, refetch };
}

export default useAsyncState;
""",
            tags=["hook", "async", "state", "typescript"],
            dependencies=["react"],
            file_path="src/hooks/useAsyncState.ts",
        )

        # API Client Foil
        self.foils["api-client"] = Foil(
            id="api-client",
            **self.FOIL_TEMPLATES["api-client"],
            content="""import axios, { AxiosError, AxiosResponse } from 'axios';

interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
}

class ApiClient {
  private axiosInstance: typeof axios;

  constructor(baseUrl: string) {
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this._setupInterceptors();
  }

  private _setupInterceptors(): void {
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.get<T>(url);
    return { data: response.data, status: response.status, statusText: response.statusText };
  }

  async post<T>(url: string, data: unknown): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.post<T>(url, data);
    return { data: response.data, status: response.status, statusText: response.statusText };
  }

  async put<T>(url: string, data: unknown): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.put<T>(url, data);
    return { data: response.data, status: response.status, statusText: response.statusText };
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.delete<T>(url);
    return { data: response.data, status: response.status, statusText: response.statusText };
  }
}

export default ApiClient;
""",
            tags=["api", "client", "axios", "typescript"],
            dependencies=["axios"],
            file_path="src/api/client.ts",
        )

        # Validation Schema Foil
        self.foils["validation-schema"] = Foil(
            id="validation-schema",
            **self.FOIL_TEMPLATES["validation-schema"],
            content="""import { z } from 'zod';

// Email validation
export const emailSchema = z
  .string()
  .email('Invalid email address')
  .min(1, 'Email is required');

// Login form schema
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// Register form schema
export const registerSchema = z.object({
  email: emailSchema,
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain an uppercase letter')
    .regex(/[a-z]/, 'Password must contain a lowercase letter')
    .regex(/[0-9]/, 'Password must contain a number'),
  confirmPassword: z.string(),
});

export const registerSchemaWithConfirmation = registerSchema.refine(
  (data) => data.password === data.confirmPassword,
  {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  }
);

export type RegisterFormData = z.infer<typeof registerSchemaWithConfirmation>;

// Profile schema
export const profileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: emailSchema.optional(),
  bio: z.string().max(500, 'Bio must be less than 500 characters').optional(),
});

export type ProfileFormData = z.infer<typeof profileSchema>;
""",
            tags=["validation", "zod", "forms", "typescript"],
            dependencies=["zod"],
            file_path="src/validation/schemas.ts",
        )

        # React Context Foil
        self.foils["react-context"] = Foil(
            id="react-context",
            **self.FOIL_TEMPLATES["react-context"],
            content="""import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

interface User {
  id: string;
  email: string;
  name: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback(async (email: string, password: string) => {
    // Implement login logic
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    setUser(data.user);
    localStorage.setItem('authToken', data.token);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('authToken');
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
""",
            tags=["context", "auth", "react", "typescript"],
            dependencies=["react"],
            file_path="src/auth/AuthContext.tsx",
        )

        # CSS Module Foil
        self.foils["css-module"] = Foil(
            id="css-module",
            **self.FOIL_TEMPLATES["css-module"],
            content="""/* src/components/Button.module.css */

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  font-weight: 500;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.button:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Variants */
.button--primary {
  background-color: #3b82f6;
  color: white;
}

.button--primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.button--secondary {
  background-color: #6b7280;
  color: white;
}

.button--secondary:hover:not(:disabled) {
  background-color: #4b5563;
}

.button--outline {
  background-color: transparent;
  border: 2px solid #3b82f6;
  color: #3b82f6;
}

.button--outline:hover:not(:disabled) {
  background-color: #3b82f6;
  color: white;
}

/* Sizes */
.button--sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

.button--lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
}

/* Full width */
.button--full {
  width: 100%;
}
""",
            tags=["css", "module", "styling", "button"],
            dependencies=[],
            file_path="src/components/Button.module.css",
        )

        # Webpack Config Foil
        self.foils["webpack-config"] = Foil(
            id="webpack-config",
            **self.FOIL_TEMPLATES["webpack-config"],
            content=r"""const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash].js',
    clean: true,
    publicPath: '/',
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@utils': path.resolve(__dirname, 'src/utils'),
    },
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader'],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
    new CleanWebpackPlugin(),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    compress: true,
    port: 3000,
    hot: true,
    historyApiFallback: true,
  },
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',
};
""",
            tags=["webpack", "config", "build", "javascript"],
            dependencies=["webpack", "ts-loader", "html-webpack-plugin"],
            file_path="webpack.config.js",
        )

    def generate_foils(
        self,
        foil_ids: Optional[List[str]] = None,
        force_typescript: bool = False,
    ) -> List[Foil]:
        """Generate Foils based on project context.

        Args:
            foil_ids: Optional list of specific Foil IDs to generate.
            force_typescript: Force TypeScript patterns even if not detected.

        Returns:
            List of generated Foils.
        """
        if foil_ids:
            return [self.foils[id] for id in foil_ids if id in self.foils]

        # Detect if TypeScript is available
        uses_typescript = force_typescript or (
            self.project_structure
            and self.project_structure.technology_stack.get("typescript")
        )

        # Generate appropriate Foils
        foils = []

        # Always include base components
        foils.append(self.foils["base-component"])

        # Add TypeScript-specific Foils if applicable
        if uses_typescript:
            foils.extend([
                self.foils["custom-hook"],
                self.foils["api-client"],
                self.foils["validation-schema"],
                self.foils["react-context"],
            ])

        # Add language-specific Foils
        foils.append(self.foils["css-module"])

        return foils

    def generate_for_project(
        self, project_structure: Optional[ProjectStructure] = None
    ) -> List[Foil]:
        """Generate Foils tailored to a specific project.

        Args:
            project_structure: The project to generate Foils for.

        Returns:
            List of Foils appropriate for the project.
        """
        if project_structure:
            self.project_structure = project_structure

        if not self.project_structure:
            # Generate generic Foils
            return self.generate_foils(force_typescript=True)

        # Check for TypeScript
        uses_typescript = self.project_structure.technology_stack.get(
            "typescript"
        )

        # Check for React
        uses_react = self.project_structure.technology_stack.get("react")

        # Build list of Foils based on project
        foils = [self.foils["base-component"]]

        if uses_typescript:
            foils.append(self.foils["custom-hook"])

        if uses_react:
            foils.append(self.foils["react-context"])

        foils.append(self.foils["css-module"])

        return foils

    def get_foils_as_code(self, foils: List[Foil]) -> str:
        """Format Foils as copy-paste ready code blocks."""
        lines = [
            "# Generated Foils",
            f"# Generated on: {datetime.now().isoformat()}",
            "",
        ]

        for foil in foils:
            lines.extend(
                [
                    f"## {foil.name} ({foil.file_path})",
                    f"{foil.description}",
                    "",
                    f"Language: {foil.language}",
                    f"Tags: {', '.join(foil.tags)}",
                    "",
                    "```" + foil.language,
                    foil.content,
                    "```",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)

    def save_foils(
        self,
        foils: List[Foil],
        output_dir: str,
        prefix: str = "foil_",
    ) -> List[str]:
        """Save Foils to files.

        Args:
            foils: List of Foils to save.
            output_dir: Directory to save files to.
            prefix: Prefix for file names.

        Returns:
            List of saved file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []

        for foil in foils:
            # Determine file extension
            ext_map = {
                "typescript": ".ts",
                "typescriptx": ".tsx",
                "javascript": ".js",
                "jsx": ".jsx",
                "css": ".css",
                "scss": ".scss",
                "html": ".html",
            }
            ext = ext_map.get(foil.language, f".{foil.language}")

            filename = f"{prefix}{foil.id}{ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                f.write(foil.content)

            saved_paths.append(filepath)

        return saved_paths

    def to_dict(self) -> Dict[str, Any]:
        """Convert Foils to dictionary format."""
        return {
            "generated_at": datetime.now().isoformat(),
            "foils": [foil.to_dict() for foil in self.foils.values()],
            "count": len(self.foils),
        }


# Global generator instance
_generator: Optional[FoilGenerator] = None


def get_generator(
    project_structure: Optional[ProjectStructure] = None,
) -> FoilGenerator:
    """Get or create the global foil generator."""
    global _generator

    if _generator is None:
        _generator = FoilGenerator(project_structure)

    return _generator
