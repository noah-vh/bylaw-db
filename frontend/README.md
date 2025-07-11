# Bylaw DB Frontend

A React TypeScript frontend for the Municipal Bylaw Database, providing a clean and professional interface for searching, viewing, and managing municipal bylaws with full source transparency and audit trails.

## Features

- **Resource Portal**: Public interface for searching and viewing bylaws
- **Admin Dashboard**: Administrative interface for managing municipalities and scraping jobs
- **Source Transparency**: Complete audit trails and source verification
- **Version History**: Track changes and updates to bylaws over time
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for navigation
- **TanStack Query** for data fetching
- **Supabase** for backend integration
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Supabase account and project

### Installation

1. Clone the repository and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy the environment file and configure your settings:
```bash
cp .env.example .env
```

4. Edit `.env` file with your Supabase credentials:
```
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

5. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure

```
src/
├── components/
│   ├── common/           # Reusable UI components
│   ├── bylaws/          # Bylaw-specific components
│   └── admin/           # Admin interface components
├── pages/               # Main page components
├── services/            # API service layer
├── types/              # TypeScript type definitions
└── styles/             # Global styles and themes
```

## Key Components

### Resource Portal
- **SearchBar**: Advanced filtering and search functionality
- **DataTable**: Responsive table with pagination for bylaw results
- **BylawDetail**: Modal for viewing complete bylaw information

### Admin Dashboard
- **Municipality Management**: CRUD operations for municipalities
- **Scraping Configuration**: Set up and monitor web scraping jobs
- **User Management**: Admin user controls and permissions

### Source Transparency
- **SourceViewer**: Display original source documents with verification
- **BylawHistory**: Version history with complete audit trails
- **Hash Verification**: Cryptographic verification of document integrity

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_SUPABASE_URL` | Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `VITE_API_BASE_URL` | Backend API base URL | No |

## Authentication

The application uses Supabase Auth for authentication. Admin users can:
- Manage municipalities
- Configure scraping jobs
- Monitor system status
- View detailed audit logs

## Deployment

1. Build the application:
```bash
npm run build
```

2. Deploy the `dist` directory to your hosting provider

3. Configure environment variables in your hosting platform

## API Integration

The frontend integrates with the backend through:
- **Supabase Client**: Direct database queries for public data
- **REST API**: Backend services for complex operations
- **Real-time Updates**: Live updates for scraping jobs and changes

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new code
3. Add proper error handling and loading states
4. Include responsive design considerations
5. Test thoroughly before submitting changes

## License

This project is licensed under the MIT License.