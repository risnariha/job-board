import React from 'react';
import { Card, Button, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { saveJob } from '../../services/jobs';

const JobCard = ({ job, onSave }) => {
  const { isAuthenticated, isJobSeeker } = useAuth();

  const handleSave = async (e