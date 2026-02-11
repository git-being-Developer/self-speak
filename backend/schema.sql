-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.ai_analyses (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  journal_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  confidence_score integer CHECK (confidence_score >= 0 AND confidence_score <= 100),
  abundance_score integer CHECK (abundance_score >= 0 AND abundance_score <= 100),
  clarity_score integer CHECK (clarity_score >= 0 AND clarity_score <= 100),
  gratitude_score integer CHECK (gratitude_score >= 0 AND gratitude_score <= 100),
  resistance_score integer CHECK (resistance_score >= 0 AND resistance_score <= 100),
  dominant_emotion text,
  goal_present boolean,
  self_doubt_present boolean,
  time_horizon text CHECK (time_horizon = ANY (ARRAY['short'::text, 'long'::text, 'vague'::text])),
  overall_tone text CHECK (overall_tone = ANY (ARRAY['calm'::text, 'anxious'::text, 'driven'::text, 'scattered'::text])),
  CONSTRAINT ai_analyses_pkey PRIMARY KEY (id),
  CONSTRAINT ai_analyses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id),
  CONSTRAINT ai_analyses_journal_id_fkey FOREIGN KEY (journal_id) REFERENCES public.journal_entries(id)
);
CREATE TABLE public.ai_usage (
  user_id uuid NOT NULL,
  week_start date NOT NULL,
  analysis_count integer DEFAULT 0,
  CONSTRAINT ai_usage_pkey PRIMARY KEY (user_id, week_start),
  CONSTRAINT ai_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);
CREATE TABLE public.journal_entries (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  entry_date date NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT journal_entries_pkey PRIMARY KEY (id),
  CONSTRAINT journal_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);
CREATE TABLE public.profiles (
  id uuid NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.subscriptions (
  user_id uuid NOT NULL,
  plan text DEFAULT 'free'::text CHECK (plan = ANY (ARRAY['free'::text, 'pro'::text])),
  started_at timestamp with time zone DEFAULT now(),
  CONSTRAINT subscriptions_pkey PRIMARY KEY (user_id),
  CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);