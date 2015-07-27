#!/bin/bash
#
#  MKMANIFEST -- Utility script to create a MANIFEST file for the repository.
#
#  A repository file has a name of the form:
#
#	<pkg>-<arch>.tar.gz
#
#  where <pkg> is the package name and <arch> is a valid IRAF architecture.
#  We create a list of available packages and create a manifest file listing
#  the package name, architecture, epoch of the file and the filename to
#  use for each architecture.  Since we allow compatible files to be used,
#  i.e. a 32-bin version can run on a 64-bit platform, we can list a
#  repository file to be used on a particular platform even if we don't have
#  the specific version here.
#
#  Repository files are assumed to contain a toplevel directory and all
#  binaries needed for a particular architecture.  Source-only packages
#  e.g. script packages, use the reserved <arch> of "universal".


unalias	ls grep egrep

set A 	= "linux64 linux redhat macintel macosx ssun sparc freebsd sunos"
set P   = `/bin/ls -1 *gz | sed -e 's/-[a-z0-9]*.tar.gz//' | egrep -v "^iraf" | egrep -v "^patch" | uniq`


# Initialize the repository files.  Note that the REPO.DESC file needs
# to be hand-crafted to provide dependency lists and package descriptions.
/bin/rm -f REPO.MANIFEST


echo "Creating manifest file ....."

echo "Arch Pkg Epoch File" | \
   awk '{ printf("# %8s  %12s  %10s  %s\n#\n",$1,$2,$3,$4) }' \
	> REPO.MANIFEST

# Foreach package in the current repository ....
foreach p ( $P )

 if ("$p" != "util") then

   # Foreach supported architecture in the system ....
   foreach a ( $A ) 

    # Get the name of the preferred file for the current package/arch
    set pf = "${p}-${a}.tar.gz"

    if (-e $pf) then
      # If preferred file exists, use it.
      set f = $pf

    else

      # Otherwise, look for compatible binary for the current arch.
      if (-e "${p}-universal.tar.gz") then
        set f = "${p}-universal.tar.gz"

      else if ("${a}" == "linux64") then	# linux64 --> linux or redhat
        set f = "${p}-linux.tar.gz"
        if (! -e "${f}") then
          set f = "${p}-redhat.tar.gz"
          if (! -e "${f}") then
            set f = "${p}-src.tar.gz"
            if (! -e "${f}") then
	      continue
            endif
          endif
        endif

      else if ("${a}" == "linux") then		# linux --> redhat
        set f = "${p}-redhat.tar.gz"
        if (! -e "${f}") then
          set f = "${p}-src.tar.gz"
          if (! -e "${f}") then
	    continue
          endif
        endif

      else if ("${a}" == "macintel") then	# macintel --> macosx
        set f = "${p}-macosx.tar.gz"
        if (! -e "${f}") then
          set f = "${p}-src.tar.gz"
          if (! -e "${f}") then
	    continue
          endif
        endif

      else if ("${a}" == "macosx") then		# macosx --> macintel
        set f = "${p}-macintel.tar.gz"
        if (! -e "${f}") then
          set f = "${p}-src.tar.gz"
          if (! -e "${f}") then
	    continue
          endif
        endif

      else
	# No repo file and no compatible file, move on...
        set f = "${p}-src.tar.gz"
        if (! -e "${f}") then
	  continue
        endif
      endif
 
    endif

    if (-e ${f}) then
      #  Note, the following command is linux-specific.
      set t = `/bin/ls -l --time-style=+%s $f | awk '{ printf ("%s", $6) }'`

      echo "${a} ${p} ${t} ${f}" | \
        awk '{ printf("%10s  %12s  %10s  %s\n", $1, $2, $3, $4) }' \
	   >> REPO.MANIFEST
    endif

 end
 endif
end



# Now create a CHECKSUMS file for the contents of the repository.  Don't be 
# picky a flag used to disable recreating checksum files.

if ($#argv == 0) then

  echo "Creating checksums file ....."
  if (`uname -s` == "Linux") then
    set cmd_bsd  = "sum -r"
    set cmd_sysv = "sum -s"
  else
    set cmd_bsd  = "cksum -o 1"
    set cmd_sysv = "cksum -o 2"
  endif

  echo 					 			>  CHECKSUMS
  echo "	------ BSD checksums ------" 			>> CHECKSUMS
  foreach i (*.gz)
    echo `$cmd_bsd $i` $i | \
      awk '{printf("  %8s %8s\t%s\n",$1,$2,$3)}'		>> CHECKSUMS
  end
  echo 					 			>> CHECKSUMS
  echo "	------ SYSV checksums ------" 			>> CHECKSUMS
  foreach i (*.gz)
    $cmd_sysv $i | awk '{printf("  %8s %8s\t%s\n",$1,$2,$3)}'	>> CHECKSUMS
  end
  echo "" 							>> CHECKSUMS

endif

echo "Done."

