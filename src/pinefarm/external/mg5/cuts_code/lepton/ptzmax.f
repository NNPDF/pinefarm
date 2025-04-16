c     cut on the pt of SFOS lepton pairs
      do i=1,nexternal-1
        if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
          do j=i+1,nexternal
            if (ipdg(i) .eq. -ipdg(j)) then
              if (((p_reco(1,i)+p(1,j))**2+
     &            (p(2,i)+p(2,j))**2) .gt. {}**2) then
                passcuts_leptons=.false.
                return
              endif
            endif
          enddo
        endif
      enddo
